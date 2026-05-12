<template>
  <AuthLayout subtitle="登录后继续">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="邮箱" prop="email">
        <el-input v-model="form.email" size="large" type="email" autocomplete="email" placeholder="name@example.com" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" size="large" show-password autocomplete="current-password" />
      </el-form-item>
      <el-button type="primary" native-type="submit" class="w-full" size="large">登录</el-button>
    </el-form>
    <p class="mt-6 text-center text-sm text-stone-500">
      没有账号？
      <router-link to="/register" class="text-teal-700 font-medium">注册</router-link>
    </p>
  </AuthLayout>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import AuthLayout from '@/components/AuthLayout.vue'
import { login } from '@/apis/auth_api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const formRef = ref<FormInstance>()
const form = reactive({ email: '', password: '' })
const rules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '邮箱格式不正确', trigger: 'blur' },
  ],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (ok) => {
    if (!ok) return
    try {
      const res = await login({ email: form.email.trim().toLowerCase(), password: form.password })
      userStore.login(res.user, res.access_token)
      ElMessage.success('登录成功')
      const redirect = route.query.redirect as string | undefined
      router.push(redirect || '/')
    } catch {
      ElMessage.error('登录失败，请检查邮箱和密码')
    }
  })
}
</script>
