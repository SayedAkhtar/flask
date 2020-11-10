
var fieldJson;

$(document).ready(function(){
  $("#loader").fadeOut(1500);
  // Variable Defination
  const userForm = $("#user-data-form");


  ConstructUserInformationForm(userForm);

  const selectFeild = $("#FieldType");
  selectFeild.on("change", function(event){
    if( event.target.value == "select" ){
        $("#select-box-option-container").removeClass("d-none");
        $("#select-box-option-container #SelectOption").prop("required", true)
    }else {
      $("#select-box-option-container").addClass("d-none");
      $("#select-box-option-container #SelectOption").prop("required", false);
      $("#select-box-option-container #SelectOption").val("");
    }
  });

  $("#downloadCSV").click((event)=>{
    $.ajax({
      url: '/download/temperature-record.csv',
      type: 'get',
      contentType: 'application/octet-stream',
      success: (response)=>{
        window.location = '/download/temperature-record.csv';
      }
    });
  });

});

function ConstructFormFeild(label, name, type, placeholder, isRequired, isDisabled=false, isEditable=false){
  return `
<div class="form-group">
  <div class="row">
    <div class="col-md-12 col-sm-12">
      <label for="${name}">${label}</label>
      <span class="input-edit-container" ${isEditable? "":'style="display:none;"'}>
        <span class="float-right" id="edit-input-field" data-fieldname="${name}"><i class="fas fa-pencil-alt text-gray-300"></i></span>
        <span class=" px-3 float-right" id="delete-input-field" data-fieldname="${name}"><i class="fas fa-trash text-gray-300"></i></span>
      </span>
    </div>
    <div class="col-md-12 col-sm-12">
      <input type="${type}" name="${name}" class="form-control form-control-user" id="${name}" required="${isRequired}" aria-describedby="emailHelp" placeholder="${placeholder}" ${isDisabled? "disabled": ""}>
    </div>
  </div>
</div>
`;
}

function ConstructSelectFeild(label, name, values, isRequired, isDisabled=false, isEditable = false){
  var option = "";
  values.forEach(function(data) {
   option = option + `<option value="${data}">${data}</option>`;
  });
  return `
<div class="form-group">
  <div class="row">
    <div class="col-md-12 col-sm-12">
      <label for="${name}">${label}</label>
      <span class="input-edit-container" ${isEditable? "":'style="display:none;"'}>
        <span class="float-right" id="edit-input-field" data-fieldname="${name}"><i class="fas fa-pencil-alt text-gray-300"></i></span>
        <span class=" px-3 float-right" id="delete-input-field" data-fieldname="${name}"><i class="fas fa-trash text-gray-300"></i></span>
      </span>
    </div>
    <div class="col-md-12 col-sm-12">
      <select name="${name}" class="form-control form-control-user" id="${name}" required="${isRequired}" ${isDisabled? "disabled": ""} >
        <option value="----" selected>Select One Feild</option>
          ${ option }
      </select>
    </div>
  </div>
</div> 
`;
}

function ConstructUserInformationForm(formSelector){

  $.getJSON('/api/fields', function (result){
    let previousContent = formSelector.html();
    formSelector.html("");
    result.data.forEach(function(data){
      if(data.values){
        formSelector.append(ConstructSelectFeild(data.label, data.name, data.values, data.required, false, false))
      }else {
        formSelector.append(ConstructFormFeild(data.label, data.name, data.type, data.placeholder, data.required, false, false));
      }
    });
    formSelector.append(previousContent);
  });
}


function resetForm(){
    $("#user-data-form").trigger("reset")
  }
