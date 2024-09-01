document.getElementById('add-item-form').addEventListener('submit', function (event) {
    event.preventDefault(); // Prevent default form submission

    let formData = new FormData(this);

    fetch('/inventory', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(data.message);
            location.reload(); // Reload the page to refresh the inventory list
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => console.error('Error:', error));
});

// Function to handle dispatching an item
function dispatchItem(itemId) {
    const dispatchQuantity = prompt("Enter the quantity to dispatch:");

    if (!dispatchQuantity || isNaN(dispatchQuantity) || dispatchQuantity <= 0) {
        alert("Please enter a valid quantity.");
        return;
    }

    fetch('/dispatch', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ id: itemId, quantity: dispatchQuantity })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert(data.message);
            location.reload(); // Reload the page to update the inventory list
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}

// Function to handle deleting an item
function deleteItem(itemId) {
    if (confirm("Are you sure you want to delete this item?")) {
        fetch('/delete_item', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id: itemId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                alert(data.message);
                location.reload(); // Reload the page to update the inventory list
            } else {
                alert('Error: ' + data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    }
}
