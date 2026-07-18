const video = document.getElementById("video");
const canvas = document.getElementById("canvas");
const status = document.getElementById("status");

async function loadModels() {

    status.innerHTML = "Loading AI Models...";

    await faceapi.nets.ssdMobilenetv1.loadFromUri("/static/models");
    await faceapi.nets.faceLandmark68Net.loadFromUri("/static/models");
    await faceapi.nets.faceRecognitionNet.loadFromUri("/static/models");

    status.innerHTML = "✅ Models Loaded";

}

async function initialize() {
    await loadModels();
    status.innerHTML = "Opening Camera...";

    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });
        video.srcObject = stream;
        status.innerHTML = "📷 Camera Ready";
    }

    catch (err) {
        status.innerHTML = "❌ Unable to access camera.";
        console.log(err);
    }
}

initialize();

async function captureImage() {

    if (!video.srcObject) {
        alert("Camera is not ready yet.");
        return;
    }

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const ctx = canvas.getContext("2d");

    ctx.drawImage(video, 0, 0);

    const image = canvas.toDataURL("image/jpeg");

    const detection = await faceapi
        .detectSingleFace(video, new faceapi.SsdMobilenetv1Options())
        .withFaceLandmarks()
        .withFaceDescriptor();

    if (!detection) {
        status.innerHTML =
            " Face not detected. Please look straight into the camera.";
        return;
    }

    fetch("/verify_face", {

        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({
            image: image,
            descriptor: Array.from(detection.descriptor)
        })

    })
        .then(res => res.json())
        .then(data => {

            if (data.success) {
                status.innerHTML = "✅ Attendance Marked Successfully";

                video.srcObject.getTracks().forEach(track => track.stop());

                setTimeout(() => {
                    window.location.href = "/officer_dashboard?attendance=success";
                }, 1500);
            }
            else {
                alert(data.message);
            }
        });
}

