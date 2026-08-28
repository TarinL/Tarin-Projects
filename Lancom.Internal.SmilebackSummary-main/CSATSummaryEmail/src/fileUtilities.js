import {promises as fs} from "node:fs";

async function loadFile(filepath) {
    try {
        let content = await fs.readFile(filepath, 'utf-8');
        return content;
    } catch (error) {
        if (error.code === 'ENOENT') {
            // File not found
            console.error(`Error: The file at path '${filepath}' was not found.`);
        } else if (error instanceof SyntaxError) {
            // JSON parsing
            console.error(`Error: The file at path '${filepath}' contains invalid JSON. Likely empty.`);
        } else {
            console.error(`Error: An unexpected error occurred while loading the file: ${error.message}`);
        }
    }
}

async function saveFile(filepath, file) {
    try {
        await fs.writeFile(filepath, file);
        console.log("File saved successfully.");
    }
    catch (error) {
        console.error(`Error: An unexpected error occurred while saving the file: ${error.message}`);
    }
}

async function saveJsonFile(filepath, data) {
    data = JSON.stringify(data);
    await saveFile(filepath, data);
}

async function loadJsonFile(filepath) {
    let content = await loadFile(filepath);
    content = JSON.parse(content);
    return content;
}

export {loadFile, saveFile, loadJsonFile, saveJsonFile};
