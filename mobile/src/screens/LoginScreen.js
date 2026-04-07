import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { useAuth } from '../context/AuthContext';
import Input from '../components/Input';
import Button from '../components/Button';

export default function LoginScreen({ navigation }) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email || !password) { setError('Please enter both email and password.'); return; }
    setLoading(true); setError('');
    try {
      const result = await login(email, password);
      if (!result.success) setError(result.error || 'Invalid email or password.');
    } catch (e) {
      setError(e.response?.data?.error || 'Login failed. Please try again.');
    } finally { setLoading(false); }
  };

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <Text style={styles.emoji}>🐕</Text>
          <Text style={styles.title}>Welcome Back</Text>
          <Text style={styles.subtitle}>Sign in to FurrButler</Text>
        </View>
        <View style={styles.form}>
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <Input label="Email" placeholder="your@email.com" value={email} onChangeText={setEmail}
            keyboardType="email-address" autoCapitalize="none" />
          <Input label="Password" placeholder="Your password" value={password} onChangeText={setPassword}
            secureTextEntry />
          <Button title="Sign In" onPress={handleLogin} loading={loading} />
          <Text style={styles.link} onPress={() => navigation.navigate('Register')}>
            Don't have an account? <Text style={styles.linkBold}>Register</Text>
          </Text>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: COLORS.background },
  container: { flexGrow: 1, justifyContent: 'center', padding: SPACING.lg },
  header: { alignItems: 'center', marginBottom: 32 },
  emoji: { fontSize: 48 },
  title: { fontSize: 28, fontWeight: '700', color: COLORS.primary, marginTop: 12 },
  subtitle: { fontSize: 16, color: COLORS.grey, marginTop: 4 },
  form: { backgroundColor: COLORS.white, borderRadius: RADIUS.lg, padding: SPACING.lg },
  error: { backgroundColor: '#fde8e8', color: COLORS.danger, padding: 12, borderRadius: RADIUS.sm, marginBottom: SPACING.md, textAlign: 'center' },
  link: { textAlign: 'center', marginTop: SPACING.lg, color: COLORS.grey, fontSize: 14 },
  linkBold: { color: COLORS.primary, fontWeight: '600' },
});
