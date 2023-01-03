function setPenIconStyle() {
    if (pause) {
        // grey pen icon in pause mode
        pen_menu_logo.contentDocument.getElementById("icon").setAttribute("fill", pencolors.GRAY);
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
