import asyncio
import websockets
import base64
import json
import sys
import os

def get_base64_from_input(input_arg: str) -> str:
    """
    Xử lý đối số đầu vào và trả về một chuỗi Base64.
    - Nếu là đường dẫn tệp nhị phân (jpg, png, wav, mp3), nó sẽ đọc và mã hóa.
    - Nếu là đường dẫn tệp văn bản (txt, b64), nó sẽ đọc nội dung bên trong.
    - Nếu không phải đường dẫn tệp, nó giả định đầu vào đã là một chuỗi Base64.
    """
    try:
        # 1. Kiểm tra xem đầu vào có phải là một đường dẫn tệp tồn tại không
        if os.path.isfile(input_arg):
            print(f"-> Đang xử lý đầu vào dưới dạng tệp: '{input_arg}'")
            # 2. Nếu là tệp, kiểm tra xem có phải tệp văn bản chứa Base64 không
            if input_arg.lower().endswith(('.txt', '.b64')):
                print("   Loại tệp: Text. Đang đọc chuỗi Base64 từ tệp...")
                with open(input_arg, "r") as f:
                    return f.read().strip()
            # 3. Nếu không, coi nó là tệp nhị phân và mã hóa nó
            else:
                print("   Loại tệp: Binary. Đang mã hóa tệp sang Base64...")
                with open(input_arg, "rb") as f:
                    binary_content = f.read()
                return base64.b64encode(binary_content).decode('utf-8')
        # 4. Nếu không phải là đường dẫn tệp, giả định nó là chuỗi Base64 thô
        else:
            print("-> Đầu vào không phải là đường dẫn tệp. Giả định đây là chuỗi Base64 thô...")
            # Một kiểm tra đơn giản có thể là độ dài, nhưng ở đây chúng ta sẽ tin tưởng đầu vào
            if len(input_arg) < 100:
                 print("   Cảnh báo: Chuỗi đầu vào có vẻ quá ngắn để là một chuỗi Base64 hợp lệ.")
            return input_arg
    except Exception as e:
        print(f"Lỗi khi xử lý đầu vào '{input_arg}': {e}")
        return ""

async def send_payload_and_receive_video(image_base64: str, audio_base64: str, output_path: str = "result/output_video.b64"):
    """
    Kết nối đến API WebSocket, gửi payload chứa chuỗi Base64,
    nhận video đã xử lý dưới dạng chuỗi Base64, và lưu nó lại.
    """
    uri = "ws://localhost:8000/ws/lipsync"

    if not image_base64 or not audio_base64:
        print("\nLỗi: Không thể tạo chuỗi Base64 từ đầu vào. Vui lòng kiểm tra lại.")
        return

    try:
        async with websockets.connect(
            uri, open_timeout=60, ping_interval=20, ping_timeout=20, max_size=20 * 1024 * 1024
        ) as websocket:
            print(f"\nĐã kết nối đến server: {uri}")

            payload = {
                "image_base64": image_base64,
                "audio_base64": audio_base64
            }

            print("Đang gửi payload đến server...")
            await websocket.send(json.dumps(payload))
            print("Đã gửi. Đang chờ phản hồi...")

            response_str = await asyncio.wait_for(websocket.recv(), timeout=300.0) # Chờ phản hồi trong 5 phút
            response_json = json.loads(response_str)

            if response_json.get("status") == "success":
                video_base64_output = response_json.get("video_base64")
                if video_base64_output:
                    with open(output_path, "w") as b64_file:
                        b64_file.write(video_base64_output)
                    print(f"\nThành công! Chuỗi Base64 của video kết quả đã được lưu tại: {output_path}")
                else:
                    print("\nLỗi: Server báo thành công nhưng không có dữ liệu video Base64.")
            else:
                error_message = response_json.get("message", "Lỗi không xác định từ server.")
                print(f"\nLỗi từ server: {error_message}")

    except Exception as e:
        print(f"\nĐã xảy ra lỗi trong quá trình kết nối hoặc xử lý: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("\nCách sử dụng: python ws_client_test.py <INPUT_ẢNH> <INPUT_ÂM_THANH> [TÊN_FILE_OUTPUT]")
        print("\n<INPUT_ẢNH> và <INPUT_ÂM_THANH> có thể là một trong ba dạng sau:")
        print("  1. Đường dẫn đến tệp gốc (ví dụ: 'my_face.jpg', 'my_voice.wav')")
        print("  2. Đường dẫn đến tệp .txt/.b64 chứa chuỗi Base64 (ví dụ: 'image.b64')")
        print("  3. Chuỗi Base64 thô (dài, thường được đặt trong dấu ngoặc kép \"...\")")
        print("\n[TÊN_FILE_OUTPUT] là tùy chọn, mặc định là 'output_video.b64'.")

    else:
        image_input_arg = sys.argv[1]
        audio_input_arg = sys.argv[2]
        output_file_path = sys.argv[3] if len(sys.argv) > 3 else "result/output_video.b64"

       
        final_image_base64 = get_base64_from_input(image_input_arg)
        
        final_audio_base64 = get_base64_from_input(audio_input_arg)

        asyncio.run(send_payload_and_receive_video(final_image_base64, final_audio_base64, output_file_path))