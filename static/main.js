const TIMEOUT = 60000;

let myId;

const getMe = () => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/me");
    xhr.timeout = TIMEOUT;
    xhr.onerror = () => {
        console.error("getMe");
    };
    xhr.ontimeout = xhr.onerror;
    xhr.onabort = xhr.onerror;
    xhr.onload = e => {
        if (e.target.status === 200) {
            try {
                myId = JSON.parse(e.target.responseText).my_id;
            } catch (error) {
                console.error(error);
            }
        } else {
            e.target.onerror();
        }
    };
    xhr.send();
};

const getMessages = (dialog, maxMessageId) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/messages");
    xhr.timeout = TIMEOUT;
    xhr.onerror = () => {
        console.error("getMessages");
    };
    xhr.ontimeout = xhr.onerror;
    xhr.onabort = xhr.onerror;
    xhr.onload = e => {
        if (e.target.status === 200) {
            let items = [];
            try {
                items = JSON.parse(e.target.responseText);
            } catch (error) {
                console.error(error);
            }

            const messages = document.getElementById("messages");
            let more;

            if (!maxMessageId) {
                clear(messages);

                messages.scrollTo({top: 0});

                more = create("div", undefined, {className: "item", id: "more", onclick: () => getMessages(dialog, nextMaxMessageId)});
                more.appendChild(create("div", "Дальше", {className: "header"}));
            } else {
                more = document.getElementById("more");
                messages.removeChild(more);
            }

            let nextMaxMessageId;
            for (const item of items) {
                const message = create("div", undefined, {className: "item"});
                if (item.photo) {
                    const image = create("img");
                    message.appendChild(image);
                    image.src = item.photo;
                }
                message.appendChild(create("div", item.sender_name, {className: "header " + (item.sender_id === myId ? "me" : "someone")}));
                message.appendChild(create("div", item.text, {className: "text"}));
                message.appendChild(create("div", item.t, {className: "footer"}));
                messages.appendChild(message);
                nextMaxMessageId = item.message_id;
            }

            messages.appendChild(more);
        } else {
            e.target.onerror();
        }
    };
    xhr.send(JSON.stringify({dialog_id: dialog.dialog_id, max_message_id: maxMessageId}));
};

const getDialogs = () => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", "/dialogs");
    xhr.timeout = TIMEOUT;
    xhr.onerror = () => {
        console.error("getDialogs");
    };
    xhr.ontimeout = xhr.onerror;
    xhr.onabort = xhr.onerror;
    xhr.onload = e => {
        if (e.target.status === 200) {
            let items = [];
            try {
                items = JSON.parse(e.target.responseText);
            } catch (error) {
                console.error(error);
            }

            const dialogs = document.getElementById("dialogs");
            clear(dialogs);

            for (const item of items) {
                const dialog = create(
                    "div",
                    undefined,
                    {
                        className: "item",
                        id: "dialog/" + item.dialog_id,
                        onclick: e => {
                            for (const child of dialogs.children) {
                                child.className = "item " + (child.id === "dialog/" + item.dialog_id ? "active" : "");
                            }
                            getMessages(item);
                        }
                    }
                );
                dialog.appendChild(create("div", item.title, {className: "header"}));
                dialog.appendChild(create("div", item.message_t, {className: "footer"}));
                dialogs.appendChild(dialog);
            }
        } else {
            e.target.onerror();
        }
    };
    xhr.send();
};
