<template>
  <AuthLayout subtitle="注册新账号（邮箱验证码）">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="邮箱" prop="email">
        <div class="flex gap-2 w-full">
          <el-input
            v-model="form.email"
            class="flex-1"
            size="large"
            type="email"
            autocomplete="email"
            placeholder="name@example.com"
          />
          <el-button
            size="large"
            :disabled="cooldown > 0 || sending"
            :loading="sending"
            @click.prevent="onSendCode"
          >
            {{ cooldown > 0 ? `${cooldown}s` : '获取验证码' }}
          </el-button>
        </div>
      </el-form-item>
      <el-form-item label="邮箱验证码" prop="code">
        <el-input
          v-model="form.code"
          size="large"
          maxlength="6"
          placeholder="6 位数字"
          autocomplete="one-time-code"
        />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" size="large" show-password autocomplete="new-password" />
      </el-form-item>
      <el-form-item label="确认密码" prop="password_confirm">
        <el-input
          v-model="form.password_confirm"
          type="password"
          size="large"
          show-password
          autocomplete="new-password"
        />
      </el-form-item>
      <el-button type="primary" native-type="submit" class="w-full" size="large">注册</el-button>
    </el-form>
    <p class="mt-6 text-center text-sm text-stone-500">
      已有账号？
      <router-link to="/login" class="text-teal-700 font-medium">登录</router-link>
    </p>
  </AuthLayout>
</template>

<script setup lang="ts">
import { onUnmounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import AuthLayout from '@/components/AuthLayout.vue'
import { register, sendRegisterCode } from '@/apis/auth_api'

const router = useRouter()
const formRef = ref<FormInstance>()
const form = reactive({ email: '', code: '', password: '', password_confirm: '' })
const sending = ref(false)
const cooldown = ref(0)
let cooldownTimer: ReturnType<typeof setInterval> | null = null

function clearCooldownTimer() {
  if (cooldownTimer) {
    clearInterval(cooldownTimer)
    cooldownTimer = null
  }
}

onUnmounted(() => clearCooldownTimer())

function startCooldown(seconds: number) {
  clearCooldownTimer()
  cooldown.value = seconds
  cooldownTimer = setInterval(() => {
    cooldown.value -= 1
    if (cooldown.value <= 0) clearCooldownTimer()
  }, 1000)
}

const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  code: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为 6 位数字', trigger: 'blur' },
    { pattern: /^\d{6}$/, message: '验证码须为 6 位数字', trigger: 'blur' },
  ],
  password: [{ required: true, min: 8, message: '密码至少 8 位', trigger: 'blur' }],
  password_confirm: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== form.password) callback(new Error('两次输入的密码不一致'))
        else callback()
      },
      trigger: 'blur',
    },
  ],
}

function parseDetail(e: unknown): string | undefined {
  const msg =
    typeof e === 'object' && e !== null && 'response' in e
      ? (e as { response?: { data?: { detail?: unknown } } }).response?.data?.detail
      : undefined
  if (typeof msg === 'string') return msg
  if (Array.isArray(msg) && msg[0] && typeof (msg[0] as { msg?: string }).msg === 'string') {
    return (msg[0] as { msg: string }).msg
  }
  return undefined
}

async function onSendCode() {
  if (!formRef.value) return
  const ok = await formRef.value.validateField('email')
  if (!ok) return
  sending.value = true
  try {
    const res = await sendRegisterCode({ email: form.email.trim().toLowerCase() })
    ElMessage.success('验证码已发送，请查收邮件')
    startCooldown(res.resend_after ?? 60)
  } catch (e: unknown) {
    ElMessage.error(parseDetail(e) ?? '发送失败')
  } finally {
    sending.value = false
  }
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (ok) => {
    if (!ok) return
    try {
      await register({
        email: form.email.trim().toLowerCase(),
        password: form.password,
        password_confirm: form.password_confirm,
        code: form.code.trim(),
      })
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } catch (e: unknown) {
      ElMessage.error(parseDetail(e) ?? '注册失败，请检查验证码与密码')
    }
  })
}
</script>
