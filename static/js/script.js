function displayForm() {
    var XHR = new XMLHttpRequest()
    XHR.open('GET', '/form/123/user')
    XHR.send()
    XHR.onload = function() {
        var res = XHR.responseText
        document.write(res)
    }
}

function sendFormData() {
    var form = document.getElementById('testForm')
    jsonData = toJSONString(form)
    console.log(jsonData)
    var XHR = new XMLHttpRequest()
    XHR.open('POST', '/api/sendjson', true)
    XHR.setRequestHeader("Content-Type", "application/json;charset=UTF-8")
    XHR.send(jsonData)
    XHR.onload = function() {
        var res = XHR.responseText
        jsonData = JSON.parse(res)
        details = markup(jsonData)
        document.getElementById('details').innerHTML = details
    }
}

function markup(info) {
    var markup = `<p><b>First Name: </b>${info["firstName"]}</p>
		<p><b>Last Name: </b>${info["lastName"]}</p>
        <p><b>Status: </b>${info["status"]}</p>`
    return markup
}

function toJSONString(form) {
    var obj = {}
    var elements = form.querySelectorAll("input, textarea")
    for (var i = 0; i < elements.length; ++i) {
        var element = elements[i]
        var name = element.name
        var value = element.value
        if (name) {
            obj[name] = value
        }
    }
    return JSON.stringify(obj)
}

window.onload=function(){
    document.getElementById('getForm').addEventListener('click', displayForm, false)
    document.getElementById('formButton').addEventListener('click', sendFormData, false)
}
