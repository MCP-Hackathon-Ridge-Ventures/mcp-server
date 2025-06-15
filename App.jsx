import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native';

export default function App() {
  const [display, setDisplay] = useState('0');
  const [previousValue, setPreviousValue] = useState(null);
  const [operation, setOperation] = useState(null);
  const [waitingForNewValue, setWaitingForNewValue] = useState(false);

  const inputNumber = (num) => {
    if (waitingForNewValue) {
      setDisplay(String(num));
      setWaitingForNewValue(false);
    } else {
      setDisplay(display === '0' ? String(num) : display + num);
    }
  };

  const inputOperation = (nextOperation) => {
    const inputValue = parseFloat(display);

    if (previousValue === null) {
      setPreviousValue(inputValue);
    } else if (operation) {
      const currentValue = previousValue || 0;
      const newValue = calculate(currentValue, inputValue, operation);

      setDisplay(String(newValue));
      setPreviousValue(newValue);
    }

    setWaitingForNewValue(true);
    setOperation(nextOperation);
  };

  const calculate = (firstValue, secondValue, operation) => {
    switch (operation) {
      case '+':
        return firstValue + secondValue;
      case '-':
        return firstValue - secondValue;
      case '×':
        return firstValue * secondValue;
      case '÷':
        return firstValue / secondValue;
      case '=':
        return secondValue;
      default:
        return secondValue;
    }
  };

  const performCalculation = () => {
    const inputValue = parseFloat(display);

    if (previousValue !== null && operation) {
      const newValue = calculate(previousValue, inputValue, operation);
      setDisplay(String(newValue));
      setPreviousValue(null);
      setOperation(null);
      setWaitingForNewValue(true);
    }
  };

  const clear = () => {
    setDisplay('0');
    setPreviousValue(null);
    setOperation(null);
    setWaitingForNewValue(false);
  };

  const inputDecimal = () => {
    if (waitingForNewValue) {
      setDisplay('0.');
      setWaitingForNewValue(false);
    } else if (display.indexOf('.') === -1) {
      setDisplay(display + '.');
    }
  };

  const toggleSign = () => {
    if (display !== '0') {
      setDisplay(display.charAt(0) === '-' ? display.substr(1) : '-' + display);
    }
  };

  const percentage = () => {
    const value = parseFloat(display);
    setDisplay(String(value / 100));
  };

  const Button = ({ onPress, text, style, textStyle }) => (
    <TouchableOpacity style={[styles.button, style]} onPress={onPress}>
      <Text style={[styles.buttonText, textStyle]}>{text}</Text>
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.displayContainer}>
        <Text style={styles.displayText} numberOfLines={1} adjustsFontSizeToFit>
          {display}
        </Text>
      </View>
      
      <View style={styles.buttonContainer}>
        <View style={styles.row}>
          <Button onPress={clear} text="C" style={styles.functionButton} textStyle={styles.functionButtonText} />
          <Button onPress={toggleSign} text="±" style={styles.functionButton} textStyle={styles.functionButtonText} />
          <Button onPress={percentage} text="%" style={styles.functionButton} textStyle={styles.functionButtonText} />
          <Button onPress={() => inputOperation('÷')} text="÷" style={styles.operatorButton} textStyle={styles.operatorButtonText} />
        </View>
        
        <View style={styles.row}>
          <Button onPress={() => inputNumber(7)} text="7" />
          <Button onPress={() => inputNumber(8)} text="8" />
          <Button onPress={() => inputNumber(9)} text="9" />
          <Button onPress={() => inputOperation('×')} text="×" style={styles.operatorButton} textStyle={styles.operatorButtonText} />
        </View>
        
        <View style={styles.row}>
          <Button onPress={() => inputNumber(4)} text="4" />
          <Button onPress={() => inputNumber(5)} text="5" />
          <Button onPress={() => inputNumber(6)} text="6" />
          <Button onPress={() => inputOperation('-')} text="-" style={styles.operatorButton} textStyle={styles.operatorButtonText} />
        </View>
        
        <View style={styles.row}>
          <Button onPress={() => inputNumber(1)} text="1" />
          <Button onPress={() => inputNumber(2)} text="2" />
          <Button onPress={() => inputNumber(3)} text="3" />
          <Button onPress={() => inputOperation('+')} text="+" style={styles.operatorButton} textStyle={styles.operatorButtonText} />
        </View>
        
        <View style={styles.row}>
          <Button onPress={() => inputNumber(0)} text="0" style={styles.zeroButton} />
          <Button onPress={inputDecimal} text="." />
          <Button onPress={performCalculation} text="=" style={styles.operatorButton} textStyle={styles.operatorButtonText} />
        </View>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  displayContainer: {
    flex: 1,
    justifyContent: 'flex-end',
    alignItems: 'flex-end',
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  displayText: {
    fontSize: 70,
    color: '#fff',
    fontWeight: '200',
  },
  buttonContainer: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 10,
  },
  button: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#333',
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonText: {
    fontSize: 30,
    color: '#fff',
    fontWeight: '400',
  },
  functionButton: {
    backgroundColor: '#a6a6a6',
  },
  functionButtonText: {
    color: '#000',
  },
  operatorButton: {
    backgroundColor: '#ff9500',
  },
  operatorButtonText: {
    color: '#fff',
    fontSize: 35,
  },
  zeroButton: {
    width: 170,
    borderRadius: 40,
    paddingLeft: 30,
    alignItems: 'flex-start',
  },
});