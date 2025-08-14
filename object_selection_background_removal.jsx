// Photoshop Script: Object Selection and Background Removal
// Uses Object Selection Tool, with manual selection fallback

function main() {
    try {
        if (!app.documents.length) {
            alert("No document is open. Please open an image first.");
            return;
        }

        var doc = app.activeDocument;
        
        // Make sure we're working in RGB mode
        if (doc.mode != DocumentMode.RGB) {
            doc.changeMode(ChangeMode.RGB);
        }
        
        // Convert background layer to regular layer (so it supports transparency)
        var workingLayer;
        try {
            if (doc.backgroundLayer) {
                // Convert background layer to regular layer
                doc.backgroundLayer.isBackgroundLayer = false;
                workingLayer = doc.backgroundLayer;
                workingLayer.name = "Working Layer";
            } else {
                workingLayer = doc.activeLayer;
                workingLayer.name = "Working Layer";
            }
        } catch (e) {
            workingLayer = doc.activeLayer;
        }
        
        doc.activeLayer = workingLayer;
        
        // Check if there's already a selection
        var hasSelection = false;
        try {
            var bounds = doc.selection.bounds;
            hasSelection = (bounds[0] != bounds[2] && bounds[1] != bounds[3]);
        } catch (e) {
            hasSelection = false;
        }
        
        if (!hasSelection) {
            // Try multiple selection methods
            var selectionMade = false;
            
            // Method 1: Try Object Selection Tool
            try {
                // Switch to Object Selection Tool
                var objSelDesc = new ActionDescriptor();
                objSelDesc.putClass(charIDToTypeID("T   "), stringIDToTypeID("objectSelectionTool"));
                executeAction(charIDToTypeID("slct"), objSelDesc, DialogModes.NO);
                
                // Use the tool to select all objects
                var selectAllDesc = new ActionDescriptor();
                selectAllDesc.putEnumerated(stringIDToTypeID("selectionType"), stringIDToTypeID("selectionType"), stringIDToTypeID("allObjects"));
                executeAction(stringIDToTypeID("selectObject"), selectAllDesc, DialogModes.NO);
                
                // Check if selection was made
                var bounds = doc.selection.bounds;
                selectionMade = (bounds[0] != bounds[2] && bounds[1] != bounds[3]);
            } catch (e) {
                // Object Selection Tool failed
            }
            
            // Method 2: Try Select Subject if Object Selection failed
            if (!selectionMade) {
                try {
                    executeAction(stringIDToTypeID("selectSubject"), new ActionDescriptor(), DialogModes.NO);
                    var bounds = doc.selection.bounds;
                    selectionMade = (bounds[0] != bounds[2] && bounds[1] != bounds[3]);
                } catch (e) {
                    // Select Subject failed
                }
            }
            
            // Method 3: Manual selection prompt
            if (!selectionMade) {
                var proceed = confirm("Automatic selection failed. Please:\n\n1. Use the Object Selection Tool to click/drag around your subject\n2. OR use any selection tool to select the object\n3. Then click OK to continue\n\nClick Cancel to exit.");
                
                if (!proceed) {
                    return;
                }
                
                // Check if user made a selection
                try {
                    var bounds = doc.selection.bounds;
                    selectionMade = (bounds[0] != bounds[2] && bounds[1] != bounds[3]);
                } catch (e) {
                    selectionMade = false;
                }
                
                if (!selectionMade) {
                    alert("No selection detected. Please make a selection and try again.");
                    return;
                }
            }
        }
        
        // Now we have a selection - process it
        
        // Remove background (everything EXCEPT the selected object)
        try {
            // Invert selection to select background instead of object
            doc.selection.invert();
            
            // Delete the background (selected areas)
            doc.selection.clear();
            
            // Deselect
            doc.selection.deselect();
        } catch (e) {
            // Alternative method using layer mask
            try {
                // First invert the selection
                doc.selection.invert();
                
                // Add layer mask from inverted selection (hides background)
                var maskDesc = new ActionDescriptor();
                maskDesc.putEnumerated(charIDToTypeID("Nw  "), charIDToTypeID("Chnl"), charIDToTypeID("Msk "));
                maskDesc.putEnumerated(charIDToTypeID("At  "), charIDToTypeID("Chnl"), charIDToTypeID("Slct"));
                executeAction(charIDToTypeID("Mk  "), maskDesc, DialogModes.NO);
            } catch (e2) {
                alert("Could not remove background. Try using a layer instead of background layer.");
            }
        }
        
        
        // Trim transparent pixels
        try {
            doc.trim(TrimType.TRANSPARENT, true, true, true, true);
        } catch (e) {
            // Trim might fail if object fills canvas
        }
        
        // Save file
        var saveFile = File.saveDialog("Save PNG file", "*.png");
        if (!saveFile) {
            return;
        }
        
        if (!saveFile.name.match(/\.png$/i)) {
            saveFile = new File(saveFile.path + "/" + saveFile.name + ".png");
        }
        
        var pngOptions = new PNGSaveOptions();
        pngOptions.compression = 6;
        pngOptions.interlaced = false;
        
        doc.saveAs(saveFile, pngOptions, true, Extension.LOWERCASE);
        
        alert("Background removed and saved as: " + saveFile.name);
        
    } catch (error) {
        alert("Error: " + error.message);
    }
}

// Run the script
main();