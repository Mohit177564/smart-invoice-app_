function uploadFile() {
    let fileInput = document.getElementById("file-input");
    let file = fileInput.files[0];

    if (!file) {
        alert("Please upload a file!");
        return;
    }

    let formData = new FormData();
    formData.append("file", file);

    fetch("/extract", { method: "POST", body: formData })
        .then(response => response.json())
        .then(data => {
            console.log("Extracted Data:", data); // ✅ Debugging Log

            let output = document.getElementById("output");

            // ✅ Check for "Unknown" values and replace them with "N/A"
            let invoiceNo = data.invoice_number && data.invoice_number !== "Unknown" ? data.invoice_number : "N/A";
            let date = data.date && data.date !== "Unknown" ? data.date : "N/A";
            let amount = data.amount && data.amount !== "Unknown" ? data.amount : "N/A";
            let vendor = data.vendor && data.vendor !== "Unknown" ? data.vendor : "N/A";

            output.innerHTML = `
                <h3>Extracted Data:</h3>
                <table>
                    <tr><td><strong>Invoice No:</strong></td><td>${invoiceNo}</td></tr>
                    <tr><td><strong>Date:</strong></td><td>${date}</td></tr>
                    <tr><td><strong>Amount:</strong></td><td>${amount}</td></tr>
                    <tr><td><strong>Vendor:</strong></td><td>${vendor}</td></tr>
                </table>
                <button onclick='saveInvoice("${encodeURIComponent(JSON.stringify(data))}")'>Save Invoice</button>
            `;
        })
        .catch(error => {
            console.error("Error:", error);
            alert("Failed to extract data. Please try again.");
        });
}

function saveInvoice(encodedInvoice) {
    let invoice = JSON.parse(decodeURIComponent(encodedInvoice));

    fetch("/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(invoice)
    })
    .then(response => response.json())
    .then(data => {
        console.log("Saved Invoice:", data);
        loadInvoices();
    })
    .catch(error => {
        console.error("Save Error:", error);
        alert("Failed to save invoice.");
    });
}

function loadInvoices() {
    fetch("/get_saved")
        .then(response => response.json())
        .then(invoices => {
            console.log("Loaded Invoices:", invoices); // ✅ Debugging Log
            let tableBody = document.querySelector("#invoice-table tbody");
            tableBody.innerHTML = "";

            invoices.forEach(inv => {
                let row = `<tr>
                    <td>${inv.invoice_number || "N/A"}</td>
                    <td>${inv.date || "N/A"}</td>
                    <td>${inv.amount || "N/A"}</td>
                    <td><button onclick="deleteInvoice('${inv.invoice_number}')">Delete</button></td>
                </tr>`;
                tableBody.innerHTML += row;
            });
        })
        .catch(error => {
            console.error("Load Error:", error);
            alert("Failed to load saved invoices.");
        });
}

function deleteInvoice(invoiceNumber) {
    fetch("/delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ "invoice_number": invoiceNumber })
    })
    .then(response => response.json())
    .then(data => {
        console.log("Deleted Invoice:", data);
        loadInvoices();
    })
    .catch(error => {
        console.error("Delete Error:", error);
        alert("Failed to delete invoice.");
    });
}

function downloadExcel() {
    window.location.href = "/download";
}

window.onload = loadInvoices;
