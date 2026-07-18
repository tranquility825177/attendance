const status = document.getElementById("status");

function onScanSuccess(decodedText, decodedResult) {

    status.innerHTML = "QR Verified";
    html5QrCode.stop();
    const parts = decodedText.split("|");

    if (parts.length !== 2) {
        status.innerHTML = "Invalid QR";
        return;
    }

    fetch("/verify_qr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            employee_id: parts[0],
            token: parts[1]
        })
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                window.location = "/capture_face";
            }
            else {
                status.innerHTML = "Invalid QR";
            }
        });
}

const html5QrCode = new Html5Qrcode("reader");
html5QrCode.start({ facingMode: "environment" },{fps: 10,qrbox: 250},onScanSuccess);