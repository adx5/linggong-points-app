<!-- (岗位风控：AI预警 + 举报核实 + 移交公文) -->
<template>
  <div class="risk-page">
    <div class="header">
      <h2>岗位风控中心</h2>
      <p>AI 穿透研判 · 守护平台安全</p>
    </div>

    <div class="tabs">
      <div class="tab" :class="{ active: currentTab === 'ai' }" @click="currentTab = 'ai'">AI 预警池</div>
      <div class="tab" :class="{ active: currentTab === 'report' }" @click="currentTab = 'report'">信息举报</div>
      <div class="tab" :class="{ active: currentTab === 'revisit' }" @click="currentTab = 'revisit'">跟踪回访</div>
    </div>

    <!-- 1. AI 预警池列表 (省略，和之前一样) -->
    <div v-if="currentTab === 'ai'" class="list-content">
       <!-- 原有AI列表，这里略过，保持你现在的即可 -->
       <div class="empty">点击下方举报Tab体验新流程</div>
    </div>

    <!-- 2. 信息举报池 -->
    <div v-if="currentTab === 'report'" class="list-content">
      <div class="card" v-for="report in reports" :key="report.id" @click="openReportDetail(report)">
        <div class="header-row">
          <h3 class="text-red">⚠️ {{ report.reason }}</h3>
          <span class="status pending">待核实</span>
        </div>
        <div class="info-row"><span>档案号：</span>{{ report.file_no }}</div>
        <div class="info-row"><span>被举报岗位：</span>{{ report.job_title }}</div>
        <div class="arrow-hint">点击调取证据与处理 ></div>
      </div>
      <div v-if="reports.length === 0" class="empty">暂无待核实举报</div>
    </div>

    <!-- 3. 违规处理跟踪回访 (略，和之前一样) -->
    <div v-if="currentTab === 'revisit'" class="list-content">
       <!-- ... -->
    </div>

    <!-- 🚨 举报处理弹窗 -->
    <div v-if="reportModal.show" class="modal-overlay" @click.self="reportModal.show = false">
      <div class="modal-content">
        <h3>举报工单核实</h3>
        <div class="file-no">档案号：{{ reportModal.item.file_no }}</div>

        <div class="evidence-box">
          <p><span>被举报岗位：</span>{{ reportModal.item.job_title }}</p>
          <p><span>举报描述：</span>{{ reportModal.item.desc }}</p>
          <div class="img-placeholder">🖼️ 求职者上传的聊天/转账截图预览区</div>
        </div>

        <!-- 🚨 功能1：对文字本身进行 AI 一键复检 -->
        <div class="action-row">
          <button class="btn-ai" @click="runAICheck(reportModal.item)">🤖 对岗位文字进行 AI 复检</button>
        </div>

        <!-- 🚨 功能2：分流处理 -->
        <div class="modal-btns">
          <button class="btn-cancel" @click="reportModal.show = false">关闭</button>
          <button class="btn-reject" @click="banJob(reportModal.item)">文字违规·强制下架</button>
          <button class="btn-warn" @click="openTransferModal(reportModal.item)">线下违规·转交办理</button>
        </div>
      </div>
    </div>

    <!-- 🚨 移交材料生成弹窗 -->
    <div v-if="transferModal.show" class="modal-overlay" @click.self="transferModal.show = false">
      <div class="modal-content official-doc">
        <h3>涉嫌违法线索移交单</h3>
        <div class="doc-content">
          <p><strong>档案号：</strong>{{ transferModal.item.file_no }}</p>
          <p><strong>受移送机关：</strong>市劳动保障监察支队 / 公安局经侦大队</p>
          <p><strong>线索摘要：</strong>平台收到多名求职者举报，被举报岗位【{{ transferModal.item.job_title }}】存在线下收取大额押金后失联的行为。</p>
          <p><strong>移交材料清单：</strong></p>
          <ul>
            <li>1. 求职者举报工单及聊天截图（已脱敏）</li>
            <li>2. 企业后台注册信息及操作日志</li>
            <li>3. 该岗位发布时的 AI 审核报告</li>
          </ul>
          <p class="doc-footer">XX市零工市场平台风控中心<br>{{ currentDate }}</p>
        </div>
        <div class="modal-btns">
          <button class="btn-cancel" @click="transferModal.show = false">取消</button>
          <button class="btn-pass" @click="confirmTransfer">一键生成并打印移交函</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const currentTab = ref('report')
const currentDate = new Date().toLocaleDateString()

const reports = ref([
  { id: 1, file_no: 'JB-20231024-001', reason: '要求交押金', job_title: '高薪日结兼职', desc: 'HR让我加微信交了100块钱服装费，结果把我拉黑了。' },
  { id: 2, file_no: 'JB-20231024-002', reason: '虚假高薪', job_title: '外卖骑手直招', desc: '去了之后根本不是这个薪资，纯纯骗人。' }
])

const reportModal = reactive({ show: false, item: {} })
const transferModal = reactive({ show: false, item: {} })

const openReportDetail = (item) => { reportModal.item = item; reportModal.show = true }

// 🚨 模拟 AI 复检文字
const runAICheck = (item) => {
  window.$toast('AI 引擎正在穿透分析该岗位内容...')
  setTimeout(() => {
    window.alert(`【AI 复检报告】\n档案号：${item.file_no}\n\n风险指数：90分 (高危)\n风险点：\n1. 标题存在极度夸大词汇\n2. 简介中存在诱导加私信话术\n\n建议：立即下架并限制该企业发帖权限。`)
  }, 1000)
}

// 🚨 强制下架（文字违规）
const banJob = (item) => {
  if (window.confirm('确认该岗位文字违规，强制下架？')) {
    window.$toast('岗位已下架，已通知发帖企业。')
    reportModal.show = false
  }
}

// 🚨 转交线下
const openTransferModal = (item) => {
  reportModal.show = false
  transferModal.item = item
  transferModal.show = true
}

const confirmTransfer = () => {
  window.$toast('移交材料已生成，请线下对接有关部门。')
  transferModal.show = false
}
</script>

<style scoped>
/* 基础样式同前 */
.risk-page { min-height: 100vh; background: #f0f4f8; padding-bottom: 80px; }
.header { background: #0052d9; padding: 30px 20px 20px; color: #ffffff; }
.header h2 { font-size: 20px; margin-bottom: 4px; }
.header p { font-size: 13px; opacity: 0.8; }
.tabs { display: flex; background: #ffffff; border-bottom: 1px solid #e5e7eb; position: sticky; top: 0; z-index: 99; }
.tab { flex: 1; text-align: center; padding: 14px 0; font-size: 14px; color: #6b7280; cursor: pointer; font-weight: bold; }
.tab.active { color: #0052d9; border-bottom: 2px solid #0052d9; }
.list-content { padding: 16px; }
.card { background: #ffffff; border-radius: 12px; padding: 16px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.02); cursor: pointer; border: 1px solid transparent; }
.card:active { border-color: #0052d9; }
.header-row { display: flex; justify-content: space-between; margin-bottom: 10px; }
.header-row h3 { font-size: 16px; }
.status.pending { background: #fffbeb; color: #f59e0b; font-size: 12px; padding: 2px 6px; border-radius: 4px; font-weight: bold; }
.info-row { font-size: 13px; color: #4b5563; margin-bottom: 6px; }
.info-row span { color: #9ca3af; }
.arrow-hint { text-align: right; font-size: 12px; color: #0052d9; margin-top: 8px; }
.empty { text-align: center; color: #9ca3af; padding: 40px; font-size: 14px; }
.text-red { color: #ef4444; }

/* 弹窗通用 */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.6); z-index: 999; display: flex; justify-content: center; align-items: center; }
.modal-content { background: #ffffff; width: 90%; border-radius: 12px; padding: 20px; }
.modal-content h3 { font-size: 18px; color: #1f2937; margin-bottom: 8px; text-align: center; }
.file-no { text-align: center; font-size: 13px; color: #6b7280; margin-bottom: 16px; }

/* 详情证据区 */
.evidence-box { background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; margin-bottom: 16px; }
.evidence-box p { font-size: 14px; color: #333; margin-bottom: 8px; line-height: 1.5; }
.evidence-box span { color: #6b7280; }
.img-placeholder { height: 100px; background: #e2e8f0; display: flex; justify-content: center; align-items: center; color: #64748b; font-size: 13px; border-radius: 6px; border: 1px dashed #cbd5e1; margin-top: 8px; }

/* 操作区 */
.action-row { margin-bottom: 16px; }
.btn-ai { width: 100%; background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; padding: 12px; border-radius: 6px; font-weight: bold; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 6px; }
.btn-ai:active { background: #dbeafe; }
.modal-btns { display: flex; gap: 10px; }
.modal-btns button { flex: 1; padding: 12px 8px; border-radius: 6px; font-weight: bold; border: none; cursor: pointer; font-size: 13px; }
.btn-cancel { background: #f3f4f6; color: #4b5563; }
.btn-reject { background: #fef2f2; color: #ef4444; border: 1px solid #fecaca; }
.btn-warn { background: #fffbeb; color: #f59e0b; border: 1px solid #fde68a; }
.btn-pass { background: #0052d9; color: #fff; }

/* 移交公文样式 */
.official-doc { background: #fffdf5; border: 2px solid #fde68a; }
.official-doc h3 { color: #b45309; letter-spacing: 2px; border-bottom: 2px solid #b45309; padding-bottom: 10px; }
.doc-content { font-size: 14px; color: #374151; line-height: 1.8; margin-bottom: 20px; }
.doc-content ul { padding-left: 20px; margin-top: 8px; }
.doc-footer { text-align: right; margin-top: 30px; font-weight: bold; }
</style>