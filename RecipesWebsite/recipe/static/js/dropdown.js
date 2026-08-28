function dropdown(target_element_id) {
    if (!target_element_id)
        return;
    var element = document.getElementById(target_element_id);
    element.classList.toggle("hidden");
}

function proxyFormChanged() {
    proxyFormBoundsChecking();
    copyFromProxyForm();
}

function proxyFormBoundsChecking() {
    var fields = ['min_rating', 'max_rating', 'min_nutrition', 'max_nutrition'];
    var proxy_form = document.getElementById('proxy_form');
    var fieldReferences = [];

    fields.forEach((field) => {
        var proxy_field = getFormField(proxy_form, field);

        if (proxy_form != null) {
            fieldReferences.push(proxy_field);
        }
    });

    if (fieldReferences.length == 4) {
        // min_rating > max_rating: set min to max
        if (fieldReferences[0].value > fieldReferences[1].value) {
            fieldReferences[0].value = fieldReferences[1].value;
        }

        // min_nutrition > max_nutrition: set min to max
        if (fieldReferences[2].value > fieldReferences[3].value) {
            fieldReferences[2].value = fieldReferences[3].value;
        }
    }
}

function copyFromProxyForm() {
    var fields = ['search_type', 'min_rating', 'max_rating', 'min_nutrition', 'max_nutrition'];

    var proxy_form = document.getElementById('proxy_form');
    var search_form = document.getElementById('searchbar');

    fields.forEach((field) => {
        var proxy_field = getFormField(proxy_form, field);
        var search_field = getFormField(search_form, field);

        if (proxy_form != null && search_field != null) {
            search_field.value = proxy_field.value;
        }
    });
}

function getFormField(parent, field) {
    var elements = document.getElementsByName(field);
    var return_element = null;

    elements.forEach((element) => {
        if (element.parentElement == parent || element.parentElement.parentElement == parent) {
            return_element = element;
        }
    });

    return return_element;
}