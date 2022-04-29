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

function removeDuplicates(arr) {
    var checkDict = {}
    var newArr = []
    for (let i in arr) {
        if (!checkDict[arr[i]]) {
            checkDict[arr[i]] = true;
            newArr.push(arr[i]);
        }
    }
    return newArr;
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
    var typesSelect = document.getElementById("types");
    var firstSelect = document.getElementById("first-select");
    var secondSelect = document.getElementById("second-select");

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
    var typesSelect = document.getElementById("types");
    var firstSelect = document.getElementById("first-select");
    var secondSelect = document.getElementById("second-select");
    var resultsArea = document.getElementById("resultsArea");

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
        document.getElementById("results-count").style.setProperty("display", "none");
        resultsArea.style.setProperty("display", "none");
    } else {
        document.getElementById("results-count").style.removeProperty("display");
        resultsArea.style.removeProperty("display");
    }
}

function getResults(type, first, second) {
    if (first == "all") {
        let results = [];
        loadJSON("./data/" + type + "/index.json")["data"].forEach(function(i) {
            results = results.concat(getResults(type, i, second));
        });
        results = removeDuplicates(results);
        results.sort();
        return results;
    }

    var data = loadJSON("./data/" + type + "/" + first + ".json");

    let results = [];

    if (isArray(data)) {
        for (let i in data) {
            results.push(data[i]);
        }
    } else {
        for (const [key, value] of Object.entries(data)) {
            if (key == second || second == "all") {
                for (let i in value) {
                    results.push(value[i]);
                }
            }
        }
    }

    results = removeDuplicates(results);

    results.sort();

    return results;
}

function fillTextArea() {
    let lines = getResults(document.getElementById("types").value, document.getElementById("first-select").value, document.getElementById("second-select").value);

    var resultText = "";

    for (let i in lines) {
        resultText += lines[i] + "\n";
    }

    var resultsArea = document.getElementById("resultsArea");
    resultsArea.value = resultText;
    resultsArea.scrollTop = 0;

    document.getElementById("results-count").innerText = lines.length + " results";

    that.updateUrlParameter();
    that.updateVisibility();
}

function getSecondSelectOptions(type, first) {
    if (first == "blank") {
        return [];
    }

    if (first == "all") {
        let options = [];
        loadJSON("./data/" + type + "/index.json")["data"].forEach(function(i) {
            options = options.concat(getSecondSelectOptions(type, i));
        });
        options = removeDuplicates(options);
        options.sort();
        return options;
    }

    let secondData = loadJSON("./data/" + type + "/" + first+ ".json");

    if (isArray(secondData)) {
        return [];
    }

    var options = Object.keys(secondData);
    options.sort();

    return options;
}

function firstBoxHandler() {
    if (document.getElementById("first-select").value == "blank") {
        document.getElementById("second-select").options.length = 0;
        that.updateUrlParameter();
        that.updateVisibility();
        return;
    }

    var secondSelect = document.getElementById("second-select");

    secondSelect.options.length = 0;

    var options = getSecondSelectOptions(document.getElementById("types").value, document.getElementById("first-select").value);

    if (options.length == 0) {
        that.fillTextArea();
        that.updateUrlParameter();
        that.updateVisibility();
        return;
    }

    var allOption= document.createElement("option");
    allOption.text = "All";
    allOption.value = "all";
    secondSelect.add(allOption);

    for (var i in options) {
        var dataOption= document.createElement("option");
        dataOption.text = options[i];
        dataOption.value = options[i];
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

    var firstData = loadJSON("./data/" + document.getElementById("types").value + "/index.json")

    document.getElementById("description").innerText = firstData["description"];

    var firstSelect = document.getElementById("first-select");

    firstSelect.options.length = 0;

    var blankOption= document.createElement("option");
    blankOption.text = "Select a Value";
    blankOption.value = "blank";
    firstSelect.add(blankOption);

    if (firstData["enableAll"]) {
        var allOption= document.createElement("option");
        allOption.text = firstData.allText || "All";
        allOption.value = "all";
        firstSelect.add(allOption);
    }

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
    var types = document.getElementById("types");

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

    document.getElementById("app-count").innerText = "There are currently " + loadJSON("./data/appcount.json").toLocaleString() + " Apps on Flathub";

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