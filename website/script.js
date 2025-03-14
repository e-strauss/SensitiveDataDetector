const BACKEND_URL = "http://192.168.178.68:8000";

async function postRequest(endpoint, data = {}) {
    try {
        console.log("Sending data:", JSON.stringify(data));

        const response = await fetch(`${BACKEND_URL}/${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error(`Error: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error("Request failed", error);
        return {};
    }
}

let sensitiveWordSet = new Set(); // Global state to store detected words

async function detectSensitiveInfo() {
    const textInput = document.getElementById("textInput");
    const output = document.getElementById("output");
    const text = textInput.innerText;

    console.log("Detecting sensitive info...");
    const response = await postRequest("detect", { "text": text });
    const newSensitiveWords = response.sensitive_words || [];

    // Add new words to the global set
    newSensitiveWords.forEach(word => sensitiveWordSet.add(word));

    output.innerText = `Sensitive Words: ${[...sensitiveWordSet].join(", ")}`;

    let updatedText = text;
    sensitiveWordSet.forEach(word => {
        const regex = new RegExp(`\\b${word}\\b`, 'gi'); // Match whole words case-insensitively
        updatedText = updatedText.replace(regex, `<span class="highlight">${word}</span>`);
    });

    textInput.innerHTML = updatedText; // Use innerHTML to apply the styling
    console.log("Sensitive info detection complete.");
}



async function replaceSensitiveInfo() {
    const textInput = document.getElementById("textInput");
    const output = document.getElementById("output");
    const text = textInput.innerText;

    const sensWordList = [...sensitiveWordSet];
    const joinedSensWordList = sensWordList.join(", ");
    console.log("Replacing sensitive info with placeholders...");
    const response = await postRequest("place_holder", { "text": joinedSensWordList});
    const placeholders = response.place_holders || {};


    console.log("Text:", placeholders);
    const placeholderDict = JSON.parse(placeholders)
    console.log("placeholderDict:", placeholderDict)

    let updatedText = text;
    Object.entries(placeholders).forEach(([word, placeholder]) => {
        updatedText = updatedText.replace(new RegExp(word, 'g'), placeholder);
    });
    textInput.value = updatedText;
    output.innerText = "Placeholders Applied!";
    console.log("Replacement complete.");
}

async function sayHello() {
    console.log("Calling /hello endpoint...");
    const response = await postRequest("hello");
    const message = response.message || "No response";
    document.getElementById("output").innerText = message;
    console.log(`Received message: ${message}`);
}
