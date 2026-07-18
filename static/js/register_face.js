const video = document.getElementById("video");
const captureBtn = document.getElementById("captureBtn");
const statusText = document.getElementById("faceStatus");
const descriptorInput = document.getElementById("face_descriptor");

let modelsLoaded = false;

async function loadModels() {

    statusText.innerHTML = "Loading AI Models...";

    await faceapi.nets.ssdMobilenetv1.loadFromUri("/static/models");
    await faceapi.nets.faceLandmark68Net.loadFromUri("/static/models");
    await faceapi.nets.faceRecognitionNet.loadFromUri("/static/models");

    modelsLoaded = true;
    statusText.style.color = "green";
    statusText.innerHTML = "Models Loaded";
    await new Promise(resolve => setTimeout(resolve, 800));
    await startCamera();
}

loadModels();

async function startCamera() {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({
            video: true
        });

        video.srcObject = stream;

        await new Promise((resolve) => {
            video.onloadedmetadata = () => {
                resolve();
            };
        });
        statusText.innerHTML = "📷 Camera Ready";
    }

    catch (err) {
        console.error(err);
        statusText.style.color = "red";
        statusText.innerHTML = "❌ Camera Access Denied";
    }
}

captureBtn.addEventListener("click", async () => {

    if (!modelsLoaded) {
        alert("Models are still loading.");
        return;
    }

    statusText.innerHTML = "Capturing 5 Frames...";

    statusText.style.color = "orange";

    for (let i = 3; i >= 1; i--) {
        statusText.innerHTML = "📸 Capturing in " + i;
        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    let bestDescriptor = null;
    let bestScore = 0;

    for (let i = 1; i <= 5; i++) {
        statusText.style.color = "#0b57d0";
        statusText.innerHTML = `📷 Capturing ${i}/5`;
        await new Promise(resolve => setTimeout(resolve, 500));

        const detections = await faceapi
            .detectAllFaces(
                video,
                new faceapi.SsdMobilenetv1Options()
            )
            .withFaceLandmarks()
            .withFaceDescriptors();

        if (detections.length === 0) {

            statusText.style.color = "red";
            statusText.innerHTML = "❌ No face detected";
            continue;

        }

        if (detections.length > 1) {

            statusText.style.color = "red";
            statusText.innerHTML = "❌ Multiple faces detected";
            continue;

        }

        const detection = detections[0];

        if (!detection) {
            console.log(`Frame ${i}: No face detected`);
            continue;
        }

        if (detection.detection.score > bestScore) {

            bestScore = detection.detection.score;

            bestDescriptor = detection.descriptor;

        }

    }

    if (bestDescriptor == null) {

        statusText.style.color = "red";

        statusText.innerHTML = "❌ Face Not Detected . Please look straight at the camera";

        return;

    }

    descriptorInput.value =
        JSON.stringify(Array.from(bestDescriptor));

    statusText.style.color = "green";

    statusText.innerHTML =
        `✅ Face Captured Successfully<br>
Confidence : ${(bestScore * 100).toFixed(2)}%`;

    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }

});

const form = document.querySelector("form");

form.addEventListener("submit", (e) => {

    if (descriptorInput.value === "" || descriptorInput.value.length < 10) {
        e.preventDefault();
        alert("Please capture your face before registering.");
    }

});