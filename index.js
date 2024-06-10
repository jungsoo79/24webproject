const $txt = document.querySelector(".mvtxt");
const content = "안녕하세요! \n게으른 개발자 박정수입니다:)\n 제 웹페이지에 오신 걸 환영합니다.";
let contentIndex = 0;

let typing = function () {
  $txt.innerHTML += content[contentIndex];
  contentIndex++;
  if (content[contentIndex] === "\n") {
    $txt.innerHTML += "<br />";
    contentIndex++;
  }
  if (contentIndex > content.length) {
    $txt.textContent = "";
    contentIndex = 0;
  }
};

setInterval(typing, 200);