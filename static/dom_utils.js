const clear = e => {
    while (e.firstChild) {
        e.removeChild(e.firstChild);
    }
};

const create = (tag, content, props) => {
    const res = document.createElement(tag);
    if (Array.isArray(content)) {
        for (const item of content) {
            res.appendChild(item);
        }
    } else if (content) {
        res.innerText = content;
    }
    if (props) {
        for (const prop in props) {
            if (typeof props[prop] === "object") {
                for (const key in props[prop]) {
                    res[prop][key] = props[prop][key];
                }
            } else {
                res[prop] = props[prop];
            }
        }
    }
    return res;
};

const update = (id, content, props) => {
    const res = document.getElementById(id);
    if (Array.isArray(content)) {
        clear(res);
        for (const item of content) {
            res.appendChild(item);
        }
    } else if (content) {
        res.innerText = content;
    }
    if (props) {
        for (const prop in props) {
            if (typeof props[prop] === "object") {
                for (const key in props[prop]) {
                    res[prop][key] = props[prop][key];
                }
            } else {
                res[prop] = props[prop];
            }
        }
    }
};
