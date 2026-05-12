<template>
  <AuthLayout subtitle="注册新账号（笔试演示用）">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="submit">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" size="large" autocomplete="username" />
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input v-model="form.password" type="password" size="large" show-password autocomplete="new-password" />
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
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import AuthLayout from '@/components/AuthLayout.vue'
import { register } from '@/apis/auth_api'

const router = useRouter()
const formRef = ref<FormInstance>()
const form = reactive({ username: '', password: '' })
const rules: FormRules = {
  username: [{ required: true, min: 2, message: '至少 2 个字符', trigger: 'blur' }],
  password: [{ required: true, min: 6, message: '至少 6 个字符', trigger: 'blur' }],
}

async function submit() {
  if (!formRef.value) return
  await formRef.value.validate(async (ok) => {
    if (!ok) return
    try {
      await register(form)
      ElMessage.success('注册成功，请登录')
      router.push('/login')
    } catch {
      ElMessage.error('注册失败，用户名可能已被占用')
    }
  })
}
</script>
