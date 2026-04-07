import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { COLORS, SPACING, RADIUS } from '../constants/theme';
import { useAuth } from '../context/AuthContext';
import Input from '../components/Input';
import Button from '../components/Button';

export default function RegisterScreen({ navigation }) {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!email || !password) { setError('Please fill in all required fields.'); return; }
    setLoading(true); setError('');
    try {
      const result = await register(email, password, name);
      if (!result.success) setError(result.error || 'Registration failed.');
    } catch (e) {
      setError(e.response?.data?.error || 'Registration failed.');
    } finally { setLoading(false); }
  };

  return (
    <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView contentContainerStyle={styles.container}>
        <View style={styles.header}>
          <Text style={styles.emoji}>📝</Text>
          <Text style={styles.title}>Create Account</Text>
          <Text style={styles.subtitle}>Join FurrButler today</Text>
        </View>
        <View style={styles.form}>
          {error ? <Text style={styles.error}>{error}</Text> : null}
          <Input label="Full Name" placeholder="Your name" value={name} onChangeText={setName} />
          <Input label="Email" placeholder="your@email.com" value={email} onChangeText={setEmail}
            keyboardType="email-address" autoCapitalize="none" />
          <Input label="Password" placeholder="Create a password" value={password} onChangeText={setPassword}
            secureTextEntry />
          <Button title="Create Account" onPress={handleRegister} loading={loading} />
          <Text style={styles.link} onPress={() => navigation.navigate('Login')}>
            Already have an account? <Text style={styles.linkBold}>Sign In</Text>
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
