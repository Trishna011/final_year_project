import { Box } from "@chakra-ui/react";
import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";
import LandingPage from "./components/LandingPage";
import RenoType from "./components/RenoType";
import PropertySize from "./components/PropertySize";
import Location from "./components/Location";
import SqftToReno from "./components/SqftToReno";
import SqftToAdd from "./components/SqftToAdd";
import StructChanges from "./components/StructChanges";
import MaterialGrade from "./components/MaterialGrade";
import CostPage from "./components/CostPage";

const MotionBox = motion(Box);

const pageVariants = {
  initial: { opacity: 0, y: 80 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -80 },
};
const pageTransition = { duration: 0.4, ease: "easeInOut" };
export default function App() {
  const [started, setStarted] = useState(false);
  const [step, setStep] = useState(1);
  const [answers, setAnswers] = useState({});
  const clearAnswers = () => {setAnswers({});
};
  
  const handleNext = (data) => {
    
    const updatedAnswers = { ...answers, ...data };
    setAnswers(updatedAnswers);
    console.log(updatedAnswers);

    if (step < 8) {
      setStep(step + 1);
    } else {
      // ✅ After the last step, go to CostPage
      setStep(8);
    }
  } ;

  const handleBack = () => {
  if (step === 1) {
    setStarted(false);
    return;
  }

  setAnswers((prev) => {
    
    const newAnswers = { ...prev };
   
    const keys = Object.keys(newAnswers);

    const lastKey = keys[keys.length - 1];
    if (lastKey) {
      delete newAnswers[lastKey];
    }
    return newAnswers;
  });

 
  setStep(step - 1);
};

  const startOver = () => {
    setStarted(false); 
  setStep(1);        
  };


  // 👇 assign a single key for AnimatePresence to watch
  const currentKey = !started ? "landing" : `step-${step}`;

  return (
    <Box
      h="100vh"
      overflow="hidden"
      bgGradient="linear(to-br, gray.900, gray.800)"
      display="flex"
      alignItems="center"
      justifyContent="center"
    >
      {/* ✅ Progress bar at top */}
    {started && (
      <Box
        position="absolute"
        top={0}
        left={0}
        w="100%"
        zIndex={10}
        py={2}
      >
        <Box w="80%" maxW="700px" mx="auto">
          <Box
            color="whiteAlpha.800"
            textAlign="center"
            mb={1}
            fontSize="sm"
            letterSpacing="wide"
          >
            Step {step} of 9
          </Box>
          <Box
            h="10px"
            bg="gray.700"
            rounded="full"
            overflow="hidden"
          >
            <Box
              h="100%"
              bg="teal.400"
              w={`${(step / 8) * 100}%`}
              transition="width 0.5s ease-in-out"
            />
          </Box>
        </Box>
      </Box>
    )}
      
      {/* ✅ Single AnimatePresence handles all transitions */}
      <AnimatePresence mode="wait">
        <MotionBox
          key={currentKey}
          {...pageVariants}
          transition={pageTransition}
        >
          {!started ? (
            <LandingPage onStart={() => setStarted(true)} />
          ) : step === 1 ? (
            <RenoType step={step} onNext={handleNext} onBack={handleBack} />
          ) : step === 2 ? (
            <SqftToAdd step={step} onNext={handleNext} onBack={handleBack} />
          ) : step === 3 ? (
            <StructChanges step={step} onNext={handleNext} onBack={handleBack} />
          ) : step === 4 ? (
            <SqftToReno step={step} onNext={handleNext} onBack={handleBack} answers={answers} />
          ) : step === 5 ? (
            <MaterialGrade step={step} onNext={handleNext} onBack={handleBack} />
          ) : step === 6 ? (
            <PropertySize step={step} onNext={handleNext} onBack={handleBack} />
          ) : step === 7 ? (
            <Location step={step} onNext={handleNext} onBack={handleBack} answers={answers} />
          ):(
            <CostPage step={step} cost={answers.cost} onRestart={startOver} clearAnswers={clearAnswers} />
          )}
        </MotionBox>
      </AnimatePresence>
    </Box>
  );
}
