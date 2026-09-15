
(() => {
"use strict";
const $ = id => document.getElementById(id);
const $$ = s => [...document.querySelectorAll(s)];
let me = null;
let selectedRole = "student";
let selectedCategory = "Буллинг";
let quizData = [], quizIndex = 0, quizScore = 0, quizLocked = false;

function toast(msg){
  const t=$("toast"); if(!t)return;
  t.textContent=msg; t.classList.add("show");
  clearTimeout(window._toast); window._toast=setTimeout(()=>t.classList.remove("show"),1800);
}
function openModal(id){ $(id)?.classList.add("show"); }
function closeModal(id){ $(id)?.classList.remove("show"); }

async function api(url, options={}){
  const res = await fetch(url, options);
  let data={};
  try{ data=await res.json(); }catch(e){}
  return {res,data};
}

function roleLabel(role){
  return ({student:"Оқушы",parent:"Ата-ана",teacher:"Мұғалім",guest:"Қонақ"})[role]||role;
}

async function refreshMe(){
  const {data}=await api("/api/me");
  me=data.user||null;
  document.body.dataset.role=me?.role||"guest";
  applyPermissions();
}
function applyPermissions(){
  const role=me?.role||"guest", logged=!!me;
  $$(".auth-only").forEach(el=>el.classList.toggle("hidden",!logged));
  $$(".student-only").forEach(el=>el.classList.toggle("hidden",role!=="student"));
  $$(".parent-only").forEach(el=>el.classList.toggle("hidden",role!=="parent"));
  $$(".teacher-only").forEach(el=>el.classList.toggle("hidden",role!=="teacher"));
  $$(".guest-only").forEach(el=>el.classList.toggle("hidden",role!=="guest"));
  if($("topName")) $("topName").textContent=me?.full_name||"Қонақ";
  if($("topRole")) $("topRole").textContent=roleLabel(role);
  if($("sideRole")) $("sideRole").textContent=roleLabel(role);
  if(role==="teacher"){
    $("casesTitle").textContent="Оқушылардың өтініштері";
    $("casesSub").textContent="Мұғалім барлық оқушылардың өтініштерін қарай алады.";
  }else if(role==="student"){
    $("casesTitle").textContent="Менің өтініштерім";
    $("casesSub").textContent="Бұл жерде тек өз өтініштерің көрінеді.";
  }
}

function showScreen(id){
  if(id==="sos" && me && me.role!=="student"){ toast("Бұл бөлім тек оқушыға арналған"); id="home"; }

  if((id==="cases"||id==="mentor"||id==="children")&&!me){ $("authOverlay")?.classList.remove("hidden"); return; }
  if(id==="cases" && me?.role==="parent") id="children";
  if(id==="children" && me?.role!=="parent"){ toast("Бұл бөлім ата-анаға арналған"); return; }
  if(id==="dashboard" && me?.role!=="teacher"){ toast("Бұл бөлім сіздің рөліңізге қолжетімсіз"); return; }
  $$(".screen").forEach(s=>s.classList.toggle("active",s.id===id));
  $$(".navbtn").forEach(n=>n.classList.toggle("active",n.dataset.screen===id));
  if(id==="cases") loadCases("all");
  if(id==="children") loadChildren();
  if(id==="dashboard") loadStats();
  window.scrollTo({top:0,behavior:"smooth"});
}
$$(".go,.navbtn").forEach(b=>b.addEventListener("click",()=>b.dataset.screen&&showScreen(b.dataset.screen)));

$$(".role-pill").forEach(btn=>btn.addEventListener("click",()=>{
  selectedRole=btn.dataset.role;
  $$(".role-pill").forEach(x=>x.classList.remove("active")); btn.classList.add("active");
  const demo={
    student:["student","student123"],
    parent:["parent","parent123"],
    teacher:["teacher","teacher123"]
  }[selectedRole];
  $("loginUsername").value=demo[0]; $("loginPassword").value=demo[1];
}));

$("loginBtn")?.addEventListener("click",async()=>{
  const err=$("loginError"); err.classList.add("hidden");
  const {res,data}=await api("/api/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
    username:$("loginUsername").value,password:$("loginPassword").value,role:selectedRole
  })});
  if(!res.ok){err.textContent=data.error||"Кіру қатесі";err.classList.remove("hidden");return}
  $("authOverlay").classList.add("hidden"); await refreshMe(); showScreen("home"); toast("Кіру сәтті");
});

$("logoutBtn")?.addEventListener("click",async()=>{
  await api("/api/logout",{method:"POST"}); me=null; applyPermissions(); showScreen("home"); $("authOverlay").classList.remove("hidden");
});

$("openGuestCase")?.addEventListener("click",()=>openModal("caseModal"));
$("quickCaseBtn")?.addEventListener("click",()=>prefillAndOpenCase());
$("sosQuickBtn")?.addEventListener("click",()=>prefillAndOpenCase());
$("openRegister")?.addEventListener("click",()=>openModal("registerModal"));
$$(".modal-close").forEach(b=>b.addEventListener("click",()=>closeModal(b.dataset.close)));
$$(".modal").forEach(m=>m.addEventListener("click",e=>{if(e.target===m)m.classList.remove("show")}));

function prefillAndOpenCase(){
  if(me?.role==="student"){
    $("caseName").value=me.full_name||"";
    $("caseClass").value=me.class_name||"";
    $("caseAge").value=me.age||"";
    $("caseName").disabled=true; $("caseClass").disabled=true; $("caseAge").disabled=true;
  }else{
    $("caseName").disabled=false; $("caseClass").disabled=false; $("caseAge").disabled=false;
  }
  $("caseCategory").value=selectedCategory;
  openModal("caseModal");
}

$("registerBtn")?.addEventListener("click",async()=>{
  const err=$("regError"); err.classList.add("hidden");
  const payload={
    full_name:$("regName").value.trim(), class_name:$("regClass").value.trim(),
    age:$("regAge").value, username:$("regUser").value.trim(), password:$("regPass").value
  };
  const {res,data}=await api("/api/register/student",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  if(!res.ok){err.textContent=data.error||"Тіркелу қатесі";err.classList.remove("hidden");return}
  closeModal("registerModal"); $("authOverlay").classList.add("hidden"); await refreshMe(); toast("Тіркелу сәтті");
});

$("submitCase")?.addEventListener("click",async()=>{
  const err=$("caseError"); err.classList.add("hidden");
  const payload={
    student_name:$("caseName").value.trim(), class_name:$("caseClass").value.trim(),
    age:$("caseAge").value, category:$("caseCategory").value,
    description:$("caseDescription").value.trim()
  };
  const {res,data}=await api("/api/cases",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});
  if(!res.ok){err.textContent=data.error||"Өтініш жіберілмеді";err.classList.remove("hidden");return}
  closeModal("caseModal"); $("caseDescription").value="";
  toast("Өтініш жіберілді: #"+data.ticket);
  if(me) showScreen("cases");
});

$$(".sos-card").forEach(card=>card.addEventListener("click",()=>{
  selectedCategory=card.dataset.type;
  $$(".sos-card").forEach(x=>x.classList.remove("selected"));card.classList.add("selected");
  $("sosChosen").textContent=selectedCategory; $("sosFlow").classList.remove("hidden"); $("flowCaseBtn").classList.add("hidden");
}));
["dangerYes","dangerNo"].forEach(id=>$(id)?.addEventListener("click",()=>$("flowCaseBtn").classList.remove("hidden")));
$("flowCaseBtn")?.addEventListener("click",prefillAndOpenCase);

async function loadCases(status="all"){
  const root=$("caseList"); if(!root)return;
  root.innerHTML='<div class="panel">Жүктелуде...</div>';
  const {res,data}=await api("/api/cases?status="+encodeURIComponent(status));
  if(!res.ok){root.innerHTML='<div class="panel">Өтініштер қолжетімсіз.</div>';return}
  if(!data.length){root.innerHTML='<div class="panel">Әзірге өтініш жоқ.</div>';return}
  root.innerHTML=data.map(c=>`
    <article class="request-card">
      <div class="request-top"><div><h3>${esc(c.category)}</h3><div class="request-meta">#${esc(c.ticket)} · ${esc(c.created_at)}</div></div>
      <span class="status ${c.status==="solved"?"solved":"review"}">${c.status==="solved"?"Шешілді":"Қаралуда"}</span></div>
      <div class="request-desc">${esc(c.description)}</div>
      ${(me?.role==="teacher")?`<div class="private-meta"><span>👤 ${esc(c.student_name)}</span><span>🏫 ${esc(c.class_name)}</span><span>🎂 ${esc(c.age)}</span>${c.is_guest?'<span>⚡ Тіркелмей жіберілген</span>':''}</div>`:""}
    </article>`).join("");
}
$$(".case-tab").forEach(tab=>tab.addEventListener("click",()=>{
  $$(".case-tab").forEach(x=>x.classList.remove("active"));tab.classList.add("active");loadCases(tab.dataset.filter);
}));


let selectedChildId=null;
async function loadChildren(){
  const root=$("childrenList"); if(!root)return;
  root.innerHTML='<div class="panel">Жүктелуде...</div>';
  const {res,data}=await api("/api/children");
  if(!res.ok){root.innerHTML='<div class="panel">Балалар тізімі қолжетімсіз.</div>';return}
  if(!data.length){root.innerHTML='<div class="panel"><h3>Бала байланыстырылмаған</h3><p>Әкімші ата-ана аккаунтына оқушыны байланыстыруы керек.</p></div>';$("childCasesPanel")?.classList.add("hidden");return}
  root.innerHTML=data.map(ch=>`<button class="child-card" data-child-id="${ch.id}"><div class="child-avatar">🎓</div><div class="child-main"><b>${esc(ch.full_name)}</b><span>${esc(ch.class_name||"—")} сынып · ${esc(ch.age||"—")} жас</span></div><div class="child-count"><strong>${ch.case_count}</strong><small>өтініш</small></div></button>`).join("");
  $$(".child-card").forEach(btn=>btn.addEventListener("click",()=>selectChild(Number(btn.dataset.childId))));
  if(!selectedChildId||!data.some(x=>x.id===selectedChildId))selectedChildId=data[0].id;
  selectChild(selectedChildId);
}
async function selectChild(childId,status="all"){
  selectedChildId=childId;
  $$(".child-card").forEach(x=>x.classList.toggle("active",Number(x.dataset.childId)===childId));
  $("childCasesPanel")?.classList.remove("hidden");
  const root=$("childCaseList"); root.innerHTML='<div class="empty-state">Жүктелуде...</div>';
  const {res,data}=await api(`/api/children/${childId}/cases?status=${encodeURIComponent(status)}`);
  if(!res.ok){root.innerHTML='<div class="empty-state">Өтініштерді жүктеу мүмкін болмады.</div>';return}
  $("selectedChildName").textContent=data.child.full_name;
  if(!data.cases.length){root.innerHTML='<div class="empty-state">Бұл балада әзірге өтініш жоқ.</div>';return}
  root.innerHTML=data.cases.map(c=>`<article class="case-card"><div class="case-top"><b>#${esc(c.ticket)}</b><span class="status ${esc(c.status)}">${c.status==="solved"?"Шешілген":"Қаралуда"}</span></div><h3>${esc(c.category)}</h3><p>${esc(c.description)}</p><div class="private-meta"><span>🏫 ${esc(c.class_name)}</span><span>🎂 ${esc(c.age)}</span><span>🕘 ${esc(c.created_at)}</span></div></article>`).join("");
}
$$("[data-child-filter]").forEach(tab=>tab.addEventListener("click",()=>{
  $$("[data-child-filter]").forEach(x=>x.classList.remove("active"));tab.classList.add("active");
  if(selectedChildId)selectChild(selectedChildId,tab.dataset.childFilter);
}));

async function loadStats(){
  const {res,data}=await api("/api/stats");
  if(!res.ok){toast(data.error||"Статистика қолжетімсіз");return}
  $("statTotal").textContent=data.total;$("statReview").textContent=data.review;$("statSolved").textContent=data.solved;
  $("dashboardDesc").textContent="Барлық оқушылардың өтініштері бойынша статистика.";
}

$("mentorSend")?.addEventListener("click",async()=>{
  const msg=$("mentorText").value.trim(), status=$("mentorStatus");
  if(!msg){status.textContent="Хабарлама жазыңыз.";status.classList.remove("hidden");return}
  const {res,data}=await api("/api/mentor",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:msg})});
  status.textContent=res.ok?"Хабарлама жіберілді ✓":(data.error||"Қате");
  status.classList.remove("hidden"); if(res.ok)$("mentorText").value="";
});

$("aiAsk")?.addEventListener("click",async()=>{
  const text=$("aiInput").value.trim();
  if(!text){$("aiResult").innerHTML="<h3>Жағдайды жазыңыз.</h3>";return}
  $("aiAsk").disabled=true;
  $("aiResult").innerHTML="<h3>Жауап дайындалуда...</h3><p>AI серверіне сұрау жіберілді.</p>";
  const {res,data}=await api("/api/ai",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message:text})});
  $("aiAsk").disabled=false;
  if(!res.ok){
    $("aiResult").innerHTML=`<h3>AI қолжетімсіз</h3><p>${esc(data.error||"Қосылу қатесі")}</p>`;
    return;
  }
  const body=data.answer_text ? esc(data.answer_text).replaceAll("\n","<br>") : (Array.isArray(data.answer)?data.answer.map(x=>"• "+esc(x)).join("<br>"):"");
  $("aiResult").innerHTML=`<h3>🤖 ${esc(data.category||"AI навигатор")}</h3><p>${body}</p><p class="ai-note"><b>${esc(data.disclaimer||"")}</b></p>`;
});

$("startQuiz")?.addEventListener("click",loadQuiz);
async function loadQuiz(){
  $("quizCard").innerHTML='<div class="loading">Жаңа сұрақтар дайындалуда...</div>';
  const {res,data}=await api("/api/quiz?count=10&ts="+Date.now());
  if(!res.ok||!data.questions?.length){$("quizCard").innerHTML='<div class="loading">Тестті жүктеу қатесі.</div><button id="retryQuiz" class="btn primary">Қайталау</button>';$("retryQuiz").onclick=loadQuiz;return}
  quizData=data.questions;quizIndex=0;quizScore=0;renderQuiz();
}
function renderQuiz(){
  const q=quizData[quizIndex], letters=["A","B","C","D"];quizLocked=false;
  $("quizStep").textContent=`${quizIndex+1} / ${quizData.length}`;$("quizPoints").textContent=`${quizScore} ұпай`;$("quizBar").style.width=`${((quizIndex+1)/quizData.length)*100}%`;
  $("quizCard").innerHTML=`<h3>${esc(q.question)}</h3><div class="quiz-answers">${q.options.map((o,i)=>`<button class="quiz-answer" data-i="${i}"><b>${letters[i]}</b> ${esc(o)}</button>`).join("")}</div><div id="quizFeedback" class="quiz-feedback hidden"></div><button id="quizNext" class="btn primary quiz-next hidden">Келесі сұрақ →</button>`;
  $$(".quiz-answer").forEach(b=>b.addEventListener("click",()=>answerQuiz(Number(b.dataset.i),b)));
  $("quizNext").onclick=nextQuiz;
}
function answerQuiz(i,btn){
  if(quizLocked)return;quizLocked=true;const q=quizData[quizIndex],buttons=$$(".quiz-answer");buttons.forEach(b=>b.disabled=true);buttons[q.correct].classList.add("correct");
  if(i===q.correct){quizScore++;$("quizFeedback").textContent="✓ "+q.explanation}else{btn.classList.add("wrong");$("quizFeedback").textContent="Дұрыс жауап: "+q.options[q.correct]+". "+q.explanation}
  $("quizPoints").textContent=`${quizScore} ұпай`;$("quizFeedback").classList.remove("hidden");$("quizNext").classList.remove("hidden");
}
function nextQuiz(){
  quizIndex++; if(quizIndex<quizData.length){renderQuiz();return}
  $("quizBar").style.width="100%";$("quizStep").textContent="Дайын";
  $("quizCard").innerHTML=`<div class="loading"><h2>${quizScore}/${quizData.length}</h2><p>${quizScore>=8?"Өте жақсы!":"Жақсы нәтиже. Жаңа тестте басқа сұрақтар шығады."}</p></div><button id="newQuiz" class="btn primary">Жаңа тест бастау</button>`;
  $("newQuiz").onclick=loadQuiz;
}

$("search")?.addEventListener("keydown",e=>{if(e.key==="Enter"){const q=e.target.value.toLowerCase();showScreen(q.includes("тест")?"tests":q.includes("өтініш")?"cases":q.includes("көмек")?"sos":"ai")}});

function esc(v){return String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;")}
refreshMe();
})();
