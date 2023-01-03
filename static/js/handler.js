
let websocket = new WebSocket("ws://" + "localhost:6789" + "/websocket");

function handle_tool_message(message) {
    if (tools[message] == last_tool) { return; }
    last_tool = tools[message];
    // switch tool icon only if not in presentation mode
    if (!presentation) {
        pen_menu_logo = document.getElementById("pen");
        switch (last_tool) {
            case tools.ERASER:
                pen_menu_logo.data = "static/img/eraser-solid.svg";
                break;
            case tools.TIP:
                pen_menu_logo.data = "static/img/pen-solid.svg";
                break;
        }
    }
    return;
}

function handle_coordinate_message(message) {
    // Pre-increment rbI so we can use it in draw to refer to the current head.
    rbI = (rbI + 1) % RINGBUFFER_SIZE;
    ringbufferX[rbI] = message.x;
    ringbufferY[rbI] = message.y;
    ringbufferZ[rbI] = message.pressure;
    overlay(message.x * scaleX, message.y * scaleY);
    draw();
    if (debug) {
        ctx.fillStyle = "red";
        ctx.beginPath();
        ctx.fillRect(message.x * scaleX, message.y * scaleY, 2, 2);
        ctx.fill();
    }
}

websocket.onmessage = function (event) {
    // data is [x, y, pressure]
    let data = JSON.parse(event.data);
    switch (data.type) {
        case "tool":
            handle_tool_message(Object.keys(data.message)[0]);
        case "coordinates":
            handle_coordinate_message(data.message);
    }
};
