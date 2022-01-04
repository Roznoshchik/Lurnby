const copyInputToClipboard = (id) => {
    navigator.clipboard.writeText(document.getElementById(id).value);
}

const copyHrefToClipboard = (id) => {
    navigator.clipboard.writeText(document.getElementById(id).href);
}