document.getElementById('add-supplier-form').addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent default form submission

    let formData = new FormData(this);

    fetch('/suppliers', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(data.message);
            location.reload(); // Reload the page to refresh the suppliers list
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => console.error('Error:', error));
});

// Function to handle deleting a supplier
function deleteSupplier(supplierId) {
    if (confirm("Are you sure you want to delete this supplier?")) {
        fetch('/delete_supplier', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: supplierId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                location.reload(); // Reload the page to update the supplier list
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}
