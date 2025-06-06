# Real-Time Lip-Syncing WebSocket API

This project implements a real-time lip-syncing WebSocket API using a Generative AI model (Wav2Lip) to animate a person's image based on audio input.

> **Note**: This is my first project utilizing **Docker** for containerization and building a Python-based **WebSocket API** with FastAPI. I'm excited to have brought this concept to life and welcome any feedback.

## A. Features

* **WebSocket API Endpoint**: Accepts a Base64-encoded image and a Base64-encoded audio string for real-time processing.
* **AI-Powered Lip-Sync**: Utilizes the **Wav2Lip** model to generate a lip-synced video from a single static image and an audio file.
* **Base64 I/O**: Both the input (image, audio) and output (video) are handled as Base64-encoded strings as per the requirements.
* **Containerized**: Fully containerized using **Docker**, ensuring a consistent and reproducible environment.

---

## B. Prerequisites

### **1. FFmpeg Installation (Crucial!)**

Before proceeding, you **must have FFmpeg installed** on your system, and its executable must be available in your system's PATH. The application relies on FFmpeg for audio and video processing.

You can download it from the official website: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### **2. Docker Installation**

You must have Docker installed and running on your system to build and run the containerized application.

* **Docker Desktop** for Windows/macOS.
* **Docker Engine** for Linux.

---

## C. How the System Works

The system is designed as a client-server application that communicates over WebSockets.

1.  **Client-Side**: A client (like the provided `ws_client_test.py`) initiates a WebSocket connection to the server. It sends a JSON payload containing two keys:
    * `image_base64`: A Base64-encoded string of the person's image.
    * `audio_base64`: A Base64-encoded string of the audio.
2.  **Server-Side (FastAPI)**:
    * The FastAPI server receives the Base64 data.
    * It decodes the data into temporary image and audio files.
    * It then invokes the core lip-syncing logic by running the `Wav2Lip/inference.py` script as a **subprocess**. This script uses the powerful **Wav2Lip + GAN** model to generate a video where the person's lips in the image are synchronized with the provided audio.
    * The resulting output video file is read by the server.
3.  **Returning the Result**:
    * The server encodes the output video file back into a Base64 string.
    * This Base64 string is sent back to the client in a JSON response. The client can then decode this string to retrieve the final video.

---

## D.  Installation
### **Step 1: Clone the Repository**

First, clone this repository to your local machine or ensure all project files (`main.py`, `Dockerfile`, the `Wav2Lip` directory, etc.) are in a single project folder.

### **Step 2: Prepare the Pre-trained Model**

The application requires a pre-trained Wav2Lip model checkpoint to function. You can choose between two primary models, with download links available from the original Wav2Lip repository.

| Model         | Description                                       | Link to the model                                                                                        |
| :------------ | :------------------------------------------------- | :------------------------------------------------------------------------------------------------------- |
| Wav2Lip       | Highly accurate lip-sync                           | [Link](https://drive.google.com/drive/folders/153HLrqlBNxzZcHi17PEvP09kkAfzRshM?usp=share_link)           |
| Wav2Lip + GAN | Slightly inferior lip-sync, but better visual quality | [Link](https://drive.google.com/file/d/15G3U08c8xsCkOqQxE38Z2XXDnPcOptNk/view?usp=share_link) |

**Recommendation**: For the best visual quality, it is recommended to use the **Wav2Lip + GAN** model (the link above is for `Wav2Lip-SD-GAN.pt`).

After downloading your chosen model, place the downloaded weight file into the **`checkpoints`** folder, which is located inside the `Wav2Lip` directory. You can change which model to use in the `main.py` file

The final structure should look like this:

```
.
├── Wav2Lip/
│   ├── checkpoints/
│   │   └── Wav2Lip-SD-GAN.pt  <- Your downloaded model here
│   └── inference.py
├── main.py
├── Dockerfile
└── ...
```
   
---
## E. Preparing the WebSocket Client and Running with Docker for testing

### I. Running Docker
Follow these steps to build the Docker image and run the application.

#### **Step 1: Build the Docker Image**

Open a terminal or command prompt in the project's root directory (where the `Dockerfile` is located) and run the following command:

```bash
docker build -t lipsync-api .
```

This command builds a Docker image named **lipsync-api** from the `Dockerfile`. This process may take several minutes as it installs all necessary dependencies.

#### **Step 2: Run the Docker Container**

Once the image is built, run the application with this command:

**To run on CPU:**

```bash
docker run -p 8000:8000 --name lipsync-container lipsync-api
```

**To run with an NVIDIA GPU (requires NVIDIA Container Toolkit):**

```bash
docker run --gpus all -p 8000:8000 --name lipsync-container lipsync-api
```

This command starts a container named **lipsync-container** and maps port **8000** on your local machine to port **8000** inside the container. The server is now running and accessible at `ws://localhost:8000/ws/lipsync`.

#### **Step 3: Testing**
      Check the next section to understand how to test with data.

### II. Preparing the WebSocket Client
Follow these steps to prepare WebSocket and run the application.
#### **Step 1: Run the `main.py` file**

You can run this script using terminal or directly in visual studio code , pychar, etc

#### **Step 2: Testing**

This will use the `ws_client_test.py` script in order to test with image and sound data. You will find the **Testing Instruction** below

---

## F. Testing for both Docker and WebSocket client

### **Input Flexibility**

The client is designed to be flexible and can accept input in three different ways for both the image and audio arguments:

1.  **Direct File Path**: e.g., `my_image.jpg`, `my_audio.wav`
2.  **Path to a Text File**: A path to a `.txt` or `.b64` file containing the Base64 string.
3.  **Raw Base64 String**: The full Base64 string passed directly as an argument.


### **Testing Steps**
A Python test script, `ws_client_test.py`, is provided to interact with the API.
  
1.  **Ensure the server is running** in Docker as described above.

2.  **Run the client script from your terminal.** Here are examples for each input method:

    **Method A: Using original file paths (easiest)**
    The script will automatically encode the files to Base64.

    ```bash
    python ws_client_test.py <path/to/your/image.jpg> <path/to/your/audio.wav>
    ```

    **Method B: Using text files containing Base64 strings**
    
    ```bash
    python ws_client_test.py image.b64 audio.b64
    ```

    **Method C: Using Base64 strings**
    
    ```bash
    python ws_client_test.py "$IMG_B64" "$AUDIO_B64" 
    ```

3.  **Check the Output**: Upon successful execution, the script will create a file named **output_video.b64** (or the name you provide as a third argument). This text file contains the Base64-encoded string of the final video. You can use an online Base64 decoder to convert this string back into an `.mp4` file to view the result.

---

## G. Results and Future Improvements

The final result of this project successfully achieves the main objective: the lips of the person in the input image are animated to sync with the provided audio.

However, the visual quality of the generated output is not perfectly sharp or aesthetically pleasing. During my research, I found that many state-of-the-art implementations combine **Wav2Lip** with **GFPGAN** to significantly enhance the sharpness and produce high-quality, realistic lip movements.

Due to hardware and time constraints, I was unable to integrate this enhancement into the current API. A local test with a 1-minute audio clip took over 20 minutes to process on my machine, which highlighted the performance challenges of adding another deep learning model to the pipeline.

For future work, integrating a lightweight face enhancement model or optimizing the pipeline for faster performance would be the next logical step to improve the final output quality.
