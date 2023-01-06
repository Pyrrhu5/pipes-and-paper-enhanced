function setPenIconColor() {
    if (presentation) {
        // presentation icon
        pen_menu_logo.contentDocument.getElementById("icon").setAttribute("fill", pencolors.LIGHTGRAY);
    } else {
        if (last_tool == tools.TIP && penColor != pencolors.BLACK) {
            // coloured icon if coloured pen
            pen_menu_logo.contentDocument.getElementById("icon").setAttribute("fill", penColor);
        } else {
            // light grey icon if eraser or black pen
            pen_menu_logo.contentDocument.getElementById("icon").setAttribute("fill", pencolors.LIGHTGRAY);
        }
    }
}

function setPenIconImage() {
    if (presentation) {
         // presentation icon
        pen_menu_logo.data = "static/img/person-chalkboard-solid.svg";
    } else {
        // pen tool icons
        switch (last_tool) {
            case tools.ERASER:
                pen_menu_logo.data = "static/img/eraser-solid.svg";
                break;
            case tools.TIP:
                pen_menu_logo.data = "static/img/pen-solid.svg";
                break;
        }    }
}
