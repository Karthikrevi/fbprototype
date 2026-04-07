import React from 'react';
import { View, TouchableOpacity, StyleSheet } from 'react-native';
import { Feather } from '@expo/vector-icons';
import { COLORS } from '../constants/theme';

export default function StarRating({ rating, size = 20, editable, onRate }) {
  return (
    <View style={styles.row}>
      {[1, 2, 3, 4, 5].map((i) => (
        <TouchableOpacity key={i} onPress={() => editable && onRate?.(i)} disabled={!editable}>
          <Feather
            name={i <= rating ? 'star' : 'star'}
            size={size}
            color={i <= rating ? COLORS.star : COLORS.lightGrey}
            style={{ marginRight: 2 }}
          />
        </TouchableOpacity>
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: 'row', alignItems: 'center' },
});
