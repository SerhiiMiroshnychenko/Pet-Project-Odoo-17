/** @odoo-module **/

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

// Array of button configurations with colors and messages
const buttonStates = [
    {
        class: 'btn-primary',
        title: 'Ocean Blue',
        message: 'Cool! The button is blue like the ocean! 🌊',
        type: 'info'
    },
    {
        class: 'btn-success',
        title: 'Nature Green',
        message: 'Great success! The button is green like nature! 🌿',
        type: 'success'
    },
    {
        class: 'btn-warning',
        title: 'Sun Yellow',
        message: 'Warning! The button is yellow like the sun! ☀️',
        type: 'warning'
    },
    {
        class: 'btn-danger',
        title: 'Fire Red',
        message: 'Danger! The button is red like fire! 🔥',
        type: 'danger'
    },
    {
        class: 'btn-info',
        title: 'Sky Blue',
        message: 'Info! The button is light blue like the sky! ⛅',
        type: 'info'
    }
];

function getCurrentColorIndex() {
    const saved = localStorage.getItem('buttonColorIndex');
    return saved ? parseInt(saved) : 0;
}

function setCurrentColorIndex(index) {
    localStorage.setItem('buttonColorIndex', index.toString());
}

function executeCustomAction(env) {
    const notification = env.services.notification;
    
    console.log("Custom button clicked!");
    
    // Get current color index
    let currentColorIndex = getCurrentColorIndex();
    
    // Calculate next color index
    const nextColorIndex = (currentColorIndex + 1) % buttonStates.length;
    const nextState = buttonStates[nextColorIndex];
    
    // Find the button
    const button = document.querySelector('button.custom-color-button');

    if (button) {
        console.log("Button found:", button);
        
        // Remove current color class
        button.classList.remove(buttonStates[currentColorIndex].class);
        
        // Add new color class
        button.classList.add(nextState.class);
        
        // Save new index
        setCurrentColorIndex(nextColorIndex);
        
        notification.add(nextState.message, {
            title: nextState.title,
            type: nextState.type,
            sticky: false
        });
    } else {
        console.log("Button not found!");
        notification.add("Button element not found on the page", {
            title: "Warning!",
            type: "warning",
            sticky: false
        });
    }
    
    return Promise.resolve();
}

registry.category("actions").add("custom_button_action", executeCustomAction);