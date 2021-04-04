const deleteBtns = document.querySelectorAll('.deleteBtn');
for (let i = 0; i < deleteBtns.length; i++) {
    const deleteBtn = deleteBtns[i];
    deleteBtn.onclick = function (ev) {
        const venueId = ev.target.dataset['id'];
        const elem = document.getElementById(venueId);
        const msg = document.getElementById("message");
        fetch('/venues/' + venueId, {
            method: 'DELETE',
            body: JSON.stringify({
                'venue': venueId
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(function (response) {
            if (!response.ok) {
                console.log("Error", response);
            } else {
                // console.log("Success", response);
                msg.innerHTML = "Venue deleted";
                timer = setTimeout(function () {
                        msg.innerHTML = ""
                    }, 1500
                );
                elem.remove()
                window.location.href = "/";
            }
        })
    }
}