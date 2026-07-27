const form = document.getElementById("uploadForm");
const fileInput = document.getElementById("reportFile");
const fileName = document.getElementById("fileName");

fileInput.addEventListener("change", () => {

    if (fileInput.files.length > 0) {

        fileName.textContent = fileInput.files[0].name;

    }

});

form.addEventListener("submit", async (e) => {

    e.preventDefault();

    if (fileInput.files.length === 0) {

        alert("Please select a medical report.");
        return;

    }

    const formData = new FormData();

    formData.append("file", fileInput.files[0]);

    document.getElementById("loading").style.display = "block";

    try{

        const response = await fetch("/report/upload",{

            method:"POST",
            body:formData

        });

        const data = await response.json();

        if(response.ok){

            document.getElementById("loading").style.display = "none";

            document.getElementById("result").style.display="block";

            document.getElementById("analysis").innerHTML =
                data.analysis.replace(/\n/g, "<br>");

        }

        else{

            alert(data.detail || "Upload Failed");

        }

    }

    catch(err){

        console.log(err);

        alert("Server Error");

    }

});