var regex = {
  default: /^[a-zA-Z0-9]+$/,
  port: /^[0-9]+$/
};

function preventInputValue(inputVal, id, restriction) {
  var patt=regex.default;
  if(restriction) {
    patt = regex[restriction];
  }

  if(patt.test(inputVal)){
    document.getElementById(id).value = inputVal;
  }
  else{
    var txt = inputVal.slice(0, -1);
    document.getElementById(id).value = txt;
  }
}