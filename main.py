import sys
import os
import base64
import tempfile
import uuid
import asyncio
import subprocess # Để dùng cho create_subprocess_exec
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.logger import logger
import logging
import torch


# --- Configuration ---
logging.basicConfig(level=logging.INFO)
logger.setLevel(logging.INFO)

WAV2LIP_ROOT_DIR = "Wav2Lip"
WAV2LIP_INFERENCE_SCRIPT = os.path.join(WAV2LIP_ROOT_DIR, "inference.py")
CHECKPOINT_PATH_ARG = "checkpoints/Wav2Lip-SD-GAN.pt"

app = FastAPI()

wav2lip_script_exists = os.path.isfile(WAV2LIP_INFERENCE_SCRIPT)
if not wav2lip_script_exists:
    logger.error(f"Wav2Lip inference script not found at {WAV2LIP_INFERENCE_SCRIPT}. API will not function.")

@app.websocket("/ws/lipsync")
async def websocket_lipsync(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted.")

    if not wav2lip_script_exists:
        await websocket.send_json({"status": "error", "message": "LipSync processing script not available."})
        await websocket.close()
        logger.warning("Closing WebSocket connection as Wav2Lip script is not available.")
        return

    try:
        while True:
            data = await websocket.receive_json()
            logger.info("Received data from client.")

            image_base64 = data.get("image_base64")
            audio_base64 = data.get("audio_base64")

            if not image_base64 or not audio_base64:
                await websocket.send_json({"status": "error", "message": "Missing image_base64 or audio_base64."})
                logger.warning("Missing image or audio data from client.")
                continue

            try:
                image_bytes = base64.b64decode(image_base64)
                audio_bytes = base64.b64decode(audio_base64)
                logger.info("Base64 data decoded successfully.")
            except Exception as e:
                await websocket.send_json({"status": "error", "message": f"Base64 decoding error: {str(e)}"})
                logger.error(f"Base64 decoding error: {e}", exc_info=True)
                continue

            temp_dir = tempfile.gettempdir()
            unique_id = str(uuid.uuid4())
            
            input_image_filename = f"input_image_{unique_id}.png"
            input_audio_filename = f"input_audio_{unique_id}.wav"
            output_video_filename = f"output_video_{unique_id}.mp4"

            input_image_path = os.path.join(temp_dir, input_image_filename)
            input_audio_path = os.path.join(temp_dir, input_audio_filename)
            generated_video_temp_path = os.path.join(temp_dir, output_video_filename)

            try:
                with open(input_image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                logger.info(f"Input image saved to {input_image_path}")

                with open(input_audio_path, "wb") as aud_file:
                    aud_file.write(audio_bytes)
                logger.info(f"Input audio saved to {input_audio_path}")
                
                logger.info("Starting Wav2Lip inference process using subprocess...")

                # ***** THAY ĐỔI QUAN TRỌNG Ở ĐÂY *****
                # Thay vì dùng "python", chúng ta dùng sys.executable để chỉ định
                # chính xác trình thông dịch Python trong môi trường ảo.
                python_executable = sys.executable

                process = await asyncio.create_subprocess_exec(
                    python_executable, # Sử dụng đường dẫn tuyệt đối đến python.exe trong .venv
                    "inference.py",
                    "--checkpoint_path", CHECKPOINT_PATH_ARG,
                    "--face", os.path.abspath(input_image_path),
                    "--audio", os.path.abspath(input_audio_path),
                    "--outfile", os.path.abspath(generated_video_temp_path),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=WAV2LIP_ROOT_DIR # Đặt thư mục làm việc cho tiến trình con là Wav2Lip
                )

                stdout, stderr = await process.communicate()

                if process.returncode == 0:
                    logger.info(f"Wav2Lip inference completed successfully.")
                    if stderr:
                         logger.info(f"Subprocess stderr (often contains FFmpeg logs):\n{stderr.decode(errors='ignore')}")

                    if os.path.exists(generated_video_temp_path):
                        with open(generated_video_temp_path, "rb") as vid_file:
                            video_bytes = vid_file.read()
                        video_base64 = base64.b64encode(video_bytes).decode('utf-8')
                        logger.info("Output video encoded to base64.")
                        await websocket.send_json({
                            "status": "success",
                            "video_base64": video_base64
                        })
                    else:
                        await websocket.send_json({"status": "error", "message": "Output video not generated by script."})
                        logger.error(f"Output video file {generated_video_temp_path} not found after script execution.")
                        if stderr: logger.error(f"Subprocess stderr:\n{stderr.decode(errors='ignore')}")
                else:
                    error_message = f"Wav2Lip inference script failed with exit code {process.returncode}."
                    logger.error(error_message)
                    if stderr: logger.error(f"Subprocess stderr:\n{stderr.decode(errors='ignore')}")
                    await websocket.send_json({"status": "error", "message": error_message, "details": stderr.decode(errors='ignore')})

            except Exception as e:
                logger.error(f"Error during Wav2Lip subprocess or file handling: {e}", exc_info=True)
                if websocket.client_state.name == 'CONNECTED':
                    await websocket.send_json({"status": "error", "message": f"Processing error: {str(e)}"})
            finally:
                for f_path in [input_image_path, input_audio_path, generated_video_temp_path]:
                    if os.path.exists(f_path):
                        try:
                            os.remove(f_path)
                            logger.info(f"Cleaned up temporary file: {f_path}")
                        except Exception as e_clean:
                            logger.error(f"Error cleaning up temporary file {f_path}: {e_clean}", exc_info=True)
    
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed by client.")
    except Exception as e:
        logger.error(f"An unexpected error occurred in WebSocket handler: {e}", exc_info=True)
        # ... (khối xử lý lỗi cuối cùng) ...
    finally:
        logger.info("WebSocket connection handler finished.")

if __name__ == "__main__":
    import uvicorn
    # ... (các kiểm tra khởi động khác) ...
    uvicorn.run(app, host="0.0.0.0", port=8000)