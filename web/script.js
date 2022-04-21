var that = this;

function loadJSON(url) {
    var request = new XMLHttpRequest();
    request.open('GET', url, false);
    request.send(null);

    if (request.status === 200) {
        return JSON.parse(request.responseText);
    }
}

function isArray(myArray) {
    return myArray.constructor === Array;
}

function setOption(selectElement, value) {
    return [...selectElement.options].some((option, index) => {
        if (option.value == value) {
            selectElement.selectedIndex = index;
            return true;
        }
    });
}

function getSpecialChars(text) {
    text = text.replaceAll("{SLASH}", "/")
    text = text.replaceAll("{BACKSLASH}", "\\")
    text = text.replaceAll("{DOUBLEQUOTE}", "\"")
    text = text.replaceAll("{SPACE}", " ")
    text = text.replaceAll("{ASTERISK}", "*")
    return text
}

function updateUrlParameter() {
    typesSelect = document.getElementById("types");
    firstSelect = document.getElementById("first-select");
    secondSelect = document.getElementById("second-select");

    const url= new URL(window.location.href);

    if (typesSelect.value != "blank") {
        url.searchParams.set("type", typesSelect.value);
    } else {
        url.searchParams.delete("type");
    }

    if (firstSelect.options.length == 0 || firstSelect.value == "blank") {
        url.searchParams.delete("first");
    } else {
        url.searchParams.set("first", firstSelect.value);
    }

    if (secondSelect.options.length == 0) {
        url.searchParams.delete("second");
    } else {
        url.searchParams.set("second", secondSelect.value);
    }

    window.history.replaceState(null, null, url);
}

function updateVisibility() {
    typesSelect = document.getElementById("types");
    firstSelect = document.getElementById("first-select");
    secondSelect = document.getElementById("second-select");
    resultsArea = document.getElementById("resultsArea");

    if (typesSelect.value == "blank") {
        document.getElementById("description").style.setProperty("display", "none");
    } else {
        document.getElementById("description").style.removeProperty("display");
    }

    if (firstSelect.options.length == 0) {
        document.getElementById("first-span").style.setProperty("display", "none");
    } else {
        document.getElementById("first-span").style.removeProperty("display");
    }

    if (secondSelect.options.length == 0 || typesSelect.value == "blank" || firstSelect.value == "blank") {
        document.getElementById("second-span").style.setProperty("display", "none");
    } else {
        document.getElementById("second-span").style.removeProperty("display");
    }

    if (resultsArea.value.length == 0 || typesSelect.value == "blank" || firstSelect.value == "blank") {
        resultsArea.style.setProperty("display", "none");
    } else {
        resultsArea.style.removeProperty("display");
    }
}

function fillTextArea() {
    data = loadJSON("./data/" + document.getElementById("types").value + "/" + document.getElementById("first-select").value + ".json")

    var val = document.getElementById("second-select").value;

    let lines = [];

    if (isArray(data)) {
        for (let i in data) {
            lines.push(data[i]);
        }
    } else {
        for (const [key, value] of Object.entries(data)) {
            if (key == val || val == "all") {
                for (let i in value) {
                    lines.push(value[i]);
                }
            }
        }
    }

    lines.sort();

    resultText = "";

    for (let i in lines) {
        resultText += lines[i] + "\n";
    }

    document.getElementById("resultsArea").value = resultText;

    that.updateUrlParameter();
    that.updateVisibility();
}

function firstBoxHandler() {
    if (document.getElementById("first-select").value == "blank") {
        document.getElementById("second-select").options.length = 0;
        that.updateUrlParameter();
        that.updateVisibility();
        return;
    }

    secondData = loadJSON("./data/" + document.getElementById("types").value + "/" + document.getElementById("first-select").value + ".json")

    secondSelect = document.getElementById("second-select");

    secondSelect.options.length = 0;

    if (isArray(secondData)) {
        that.fillTextArea();
        return;
    }

    var allOption= document.createElement("option");
    allOption.text = "All";
    allOption.value = "all";
    secondSelect.add(allOption);

    for (var key in secondData) {
        var dataOption= document.createElement("option");
        dataOption.text = key;
        dataOption.value = key;
        secondSelect.add(dataOption);
    }

    const urlParams = new URL(window.location.href);
    urlParams.searchParams.set("first", secondSelect.value);
    window.history.replaceState(null, null, urlParams);

    that.fillTextArea();
}

function typesBoxHandler() {
    if (document.getElementById("types").value == "blank") {
        document.getElementById("first-select").options.length = 0;
        that.updateVisibility();
        return;
    }

    firstData = loadJSON("./data/" + document.getElementById("types").value + "/index.json")

    document.getElementById("description").innerText = firstData["description"];

    firstSelect = document.getElementById("first-select");

    firstSelect.options.length = 0;

    var blankOption= document.createElement("option");
    blankOption.text = "Select a Value";
    blankOption.value = "blank";
    firstSelect.add(blankOption);

    for (let i = 0; i < firstData["data"].length; i++) {
        var dataOption= document.createElement('option');
        dataOption.text = getSpecialChars(firstData["data"][i]);
        dataOption.value = firstData["data"][i];
        firstSelect.add(dataOption);
    }

    that.updateUrlParameter();
    that.updateVisibility();
}

window.onload = function() {
    var types = document.getElementById("types")

    //let response = await fetch("./data/types.json");
	let typeList = loadJSON("./data/types.json");

    var blankOption= document.createElement('option');
    blankOption.text = "Select a Type";
    blankOption.value = "blank";
    types.add(blankOption);

    for (let i = 0; i < typeList.length; i++) {
        var typeOption= document.createElement('option');
        typeOption.text = typeList[i]["name"];
        typeOption.value = typeList[i]["value"];
        types.add(typeOption);
    }

    let lastUpdated = new Date(loadJSON("./data/updated.json"));
    document.getElementById("last-updated").innerText = "Last updated at " + lastUpdated.toLocaleString();

    try {
        const url= new URL(window.location.href);
        setOption(document.getElementById("types"), url.searchParams.get("type"));
        typesBoxHandler();
        setOption(document.getElementById("first-select"), url.searchParams.get("first"));
        firstBoxHandler();
        setOption(document.getElementById("second-select"), url.searchParams.get("second"));
        fillTextArea();
    } catch (e) {
        console.log(e);
    }

    types.addEventListener("change", typesBoxHandler, false);
    document.getElementById("first-select").addEventListener("change", firstBoxHandler, false);
    document.getElementById("second-select").addEventListener("change", fillTextArea, false);
}