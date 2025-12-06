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
import Location_local from "./components/Location_local"
import BedBathCount from "./components/BedBathCount"

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
  console.log("Selected options length:", answers);
  
  const handleNext = (data) => {
    const updatedAnswers = { ...answers, ...data };
    setAnswers(updatedAnswers);

    // 👇 If RenoType step and user selected Bedroom/Bathroom → redirect to new step
    if (step === 1 && (data.renovation_type.includes("Bedroom") || data.renovation_type.includes("Bathroom"))) {
      setStep(2); // new mid-step
      return;
    }

    setStep(step + 1);
  };

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
              w={`${(step / 9) * 100}%`}
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
          style={{ width: "100%" }}
             w="100%" 
            maxW="700px"         // default width for all pages
            mx="auto"
        >
          
          {!started ? (
            <LandingPage onStart={() => setStarted(true)} />
          ) : step === 1 ? (
            <RenoType step={step} onNext={handleNext} onBack={handleBack} />
          ) : step === 2 ? (
            <BedBathCount 
              onNext={handleNext} 
              onBack={()=> setStep(1)} 
              selected={answers.renovation_type} 
            />
          ) : step === 3 ? (
            <SqftToAdd step={step} onNext={handleNext} onBack={handleBack} answers={answers} />
          ) : step === 4 ? (
            <StructChanges step={step} onNext={handleNext} onBack={handleBack} answers={answers}/>
          ) : step === 5 ? (
            <SqftToReno step={step} onNext={handleNext} onBack={handleBack} answers={answers} />
          ) : step === 6 ? (
            <MaterialGrade step={step} onNext={handleNext} onBack={handleBack} answers={answers} />
          ) : step === 7 ? (
            <PropertySize step={step} onNext={handleNext} onBack={handleBack} />
          ) : step === 8 ? (
            //<Location step={step} onNext={handleNext} onBack={handleBack} answers={answers} />
            <Location_local step={step} onNext={handleNext} onBack={handleBack} answers={answers} />
          ):(
            <CostPage step={step} cost={answers.cost} onRestart={startOver} clearAnswers={clearAnswers} />
          )}
        
      
        </MotionBox>
      </AnimatePresence>
    </Box>
  );
}
