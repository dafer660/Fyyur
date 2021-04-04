const deleteBtns = document.querySelectorAll('.deleteBtn');

for (let i = 0; i < deleteBtns.length; i++) {
    const deleteBtn = deleteBtns[i];
    deleteBtn.onclick = function (ev) {
        const song_id = ev.target.dataset['id'];
        const elem = document.getElementById(song_id);
        const msg = document.getElementById("message");
        let timer = null;
        fetch('/song/remove/' + song_id, {
            method: 'DELETE',
            body: JSON.stringify({
                'song': song_id
            }),
            headers: {
                'Content-Type': 'application/json'
            }
        }).then(function (response) {
            if (!response.ok) {
                console.log("Error", response);
            } else {
                // console.log("Success", response);
                msg.innerHTML = "Song deleted";
                timer = setTimeout(function () {
                        msg.innerHTML = ""
                    }, 1500
                );
                elem.remove()
            }
        })
    }
}