import React, { useState } from 'react';

function App() {
  const [display, setDisplay] = useState('0');
  const [previousValue, setPreviousValue] = useState(null);
  const [operation, setOperation] = useState(null);
  const [waitingForOperand, setWaitingForOperand] = useState(false);

  const inputNumber = (num) => {
    if (waitingForOperand) {
      setDisplay(String(num));
      setWaitingForOperand(false);
    } else {
      setDisplay(display === '0' ? String(num) : display + num);
    }
  };

  const inputDecimal = () => {
    if (waitingForOperand) {
      setDisplay('0.');
      setWaitingForOperand(false);
    } else if (display.indexOf('.') === -1) {
      setDisplay(display + '.');
    }
  };

  const clear = () => {
    setDisplay('0');
    setPreviousValue(null);
    setOperation(null);
    setWaitingForOperand(false);
  };

  const performOperation = (nextOperation) => {
    const inputValue = parseFloat(display);

    if (previousValue === null) {
      setPreviousValue(inputValue);
    } else if (operation) {
      const currentValue = previousValue || 0;
      const newValue = calculate(currentValue, inputValue, operation);

      setDisplay(String(newValue));
      setPreviousValue(newValue);
    }

    setWaitingForOperand(true);
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

  const handleEquals = () => {
    const inputValue = parseFloat(display);

    if (previousValue !== null && operation) {
      const newValue = calculate(previousValue, inputValue, operation);
      setDisplay(String(newValue));
      setPreviousValue(null);
      setOperation(null);
      setWaitingForOperand(true);
    }
  };

  const Button = ({ className, onClick, children }) => (
    <button
      className={`h-16 text-xl font-semibold rounded-lg transition-colors ${className}`}
      onClick={onClick}
    >
      {children}
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl p-6 w-full max-w-sm">
        <div className="mb-4">
          <div className="bg-gray-900 text-white p-4 rounded-lg text-right">
            <div className="text-3xl font-mono overflow-hidden">
              {display}
            </div>
          </div>
        </div>
        
        <div className="grid grid-cols-4 gap-3">
          <Button
            className="col-span-2 bg-gray-200 hover:bg-gray-300 text-gray-800"
            onClick={clear}
          >
            Clear
          </Button>
          <Button
            className="bg-gray-200 hover:bg-gray-300 text-gray-800"
            onClick={() => {
              if (display !== '0') {
                setDisplay(display.slice(0, -1) || '0');
              }
            }}
          >
            ⌫
          </Button>
          <Button
            className="bg-orange-500 hover:bg-orange-600 text-white"
            onClick={() => performOperation('÷')}
          >
            ÷
          </Button>

          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(7)}
          >
            7
          </Button>
          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(8)}
          >
            8
          </Button>
          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(9)}
          >
            9
          </Button>
          <Button
            className="bg-orange-500 hover:bg-orange-600 text-white"
            onClick={() => performOperation('×')}
          >
            ×
          </Button>

          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(4)}
          >
            4
          </Button>
          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(5)}
          >
            5
          </Button>
          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(6)}
          >
            6
          </Button>
          <Button
            className="bg-orange-500 hover:bg-orange-600 text-white"
            onClick={() => performOperation('-')}
          >
            -
          </Button>

          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(1)}
          >
            1
          </Button>
          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(2)}
          >
            2
          </Button>
          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(3)}
          >
            3
          </Button>
          <Button
            className="bg-orange-500 hover:bg-orange-600 text-white"
            onClick={() => performOperation('+')}
          >
            +
          </Button>

          <Button
            className="col-span-2 bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={() => inputNumber(0)}
          >
            0
          </Button>
          <Button
            className="bg-gray-300 hover:bg-gray-400 text-gray-800"
            onClick={inputDecimal}
          >
            .
          </Button>
          <Button
            className="bg-blue-500 hover:bg-blue-600 text-white"
            onClick={handleEquals}
          >
            =
          </Button>
        </div>
      </div>
    </div>
  );
}

export default App;