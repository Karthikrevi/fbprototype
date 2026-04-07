import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, SPACING } from '../constants/theme';
import Button from '../components/Button';

export default function WelcomeScreen({ navigation }) {
  return (
    <View style={styles.container}>
      <View style={styles.content}>
        <Text style={styles.emoji}>🐶🐱</Text>
        <Text style={styles.title}>FurrButler</Text>
        <Text style={styles.tagline}>Your complete pet care companion</Text>
        <Text style={styles.desc}>
          Grooming, boarding, marketplace, vet care, pet travel and more — all in one place.
        </Text>
      </View>
      <View style={styles.buttons}>
        <Button title="Get Started" onPress={() => navigation.navigate('Register')} style={styles.btn} />
        <Button title="I already have an account" onPress={() => navigation.navigate('Login')}
          variant="outline" style={[styles.btn, { borderColor: COLORS.white }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: COLORS.primary, justifyContent: 'space-between', padding: SPACING.xl },
  content: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  emoji: { fontSize: 64 },
  title: { fontSize: 40, fontWeight: '800', color: COLORS.white, marginTop: 16 },
  tagline: { fontSize: 18, color: 'rgba(255,255,255,0.9)', marginTop: 8, textAlign: 'center' },
  desc: { fontSize: 14, color: 'rgba(255,255,255,0.7)', marginTop: 16, textAlign: 'center', lineHeight: 20 },
  buttons: { paddingBottom: 40 },
  btn: { marginTop: 12 },
});
