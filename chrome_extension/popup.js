
const $ = (sel) => document.querySelector(sel);

const statusBox = $("#status");
const output = $("#output");
const copyBtn = $("#copyBtn");
const downloadBtn = $("#downloadBtn");

function setStatus(msg, show=true) {
  statusBox.textContent = msg || "";
  statusBox.style.display = show ? "block" : "none";
}

async function generateEmail(payload) {
  const endpoint = "http://localhost:8000/generate"; // 或 "http://127.0.0.1:8000/generate"
  const res = await fetch(endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("後端錯誤：" + res.status + " " + res.statusText);
  return await res.json();
}


document.getElementById("mainForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const your_company = $("#your_company").value.trim();
  const your_name = $("#your_name").value.trim();
  const your_title = $("#your_title").value.trim();
  const target_company = $("#target_company").value.trim();
  const company_profile = $("#company_profile").value.trim();

  if (!company_profile) {
    setStatus("⚠️ 請輸入公司簡介內容！");
    return;
  }

  setStatus("⌛ AI 正在產生英文信件...");
  output.textContent = "";
  copyBtn.disabled = true;
  downloadBtn.disabled = true;

  try {
    const data = await generateEmail({
      your_company, your_name, your_title, target_company, company_profile
    });
    output.textContent = data.email_body_en || "(no content)";
    copyBtn.disabled = false;
    downloadBtn.disabled = false;

    // store last filename for download convenience
    window.__lastFilename = data.filename || "Business_Dev_Email.txt";
    setStatus("✅ 產生成功！");
  } catch (err) {
    console.error(err);
    setStatus("❌ 發生錯誤：" + err.message);
  }
});

copyBtn.addEventListener("click", async () => {
  const text = output.textContent;
  if (!text) return;
  try {
    await navigator.clipboard.writeText(text);
    setStatus("📋 已複製到剪貼簿！");
  } catch {
    setStatus("❌ 複製失敗，請手動選取複製。");
  }
});

downloadBtn.addEventListener("click", () => {
  const text = output.textContent;
  if (!text) return;
  const blob = new Blob([text], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = window.__lastFilename || "Business_Dev_Email.txt";
  document.body.appendChild(a);
  a.click();
  URL.revokeObjectURL(url);
  a.remove();
});
