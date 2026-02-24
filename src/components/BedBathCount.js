import {
  Box,
  Button,
  Heading,
  VStack,
  Input,
  Text
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function BedBathCount({ onNext, onBack, selected }) {
  const [bedrooms, setBedrooms] = useState(1);
  const [bathrooms, setBathrooms] = useState(1);
  const [showError, setShowError] = useState(false);

  const isFullReno = selected.includes("Full renovation");

  const isEmpty = (bedrooms.length === 0 || bathrooms.length === 0) ;
  const isZeroOrNegative = !isEmpty && (Number(bedrooms) <= 0 || Number(bathrooms) <= 0);
  const canProceed = !isEmpty && !isZeroOrNegative;

  const handleContinue = () => {
    const data = {};

    if (!canProceed) {
      setShowError(true);
      
      return;
    }
    setShowError(false);

    if (selected.includes("Bedroom") || isFullReno) {
      data.bedrooms_to_reno = bedrooms;
    }

    if (selected.includes("Bathroom") || isFullReno) {
      data.bathrooms_to_reno = bathrooms;
    }

    onNext(data);
  };


  let errorMessage = "";
  if (showError) {
    if (isEmpty) errorMessage = "Please enter a value";
    else if (isZeroOrNegative) errorMessage = "Please enter a number greater than 0";
  }

  return (
    <MotionBox
      key="bedbath"
      initial={{ opacity: 0, y: 80 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -80 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      p={8}
      bg="white"
      rounded="2xl"
      shadow="xl"
      textAlign="center"
      maxW="700px"
      color="gray.800"
    >
      <Heading mb={8}>How many rooms?</Heading>

      <VStack spacing={6}>
        {(selected.includes("Bedroom") || isFullReno) && (
          <Box>
            <Heading fontWeight="medium" fontSize="md" color="black" mb={1}>
              Bedrooms to Renovate
            </Heading>
            <Input
              type="number"
              min={1}
              value={bedrooms}
              onChange={(e) => {
                const raw = e.target.value

                if (raw === '') return
                if (!/^\d+$/.test(raw)) return

                const value = Number(raw)

                if (value >= 0) {
                setBedrooms(value)
                }
              }}
              width="150px"
              textAlign="center"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
            />
          </Box>
        )}

        {(selected.includes("Bathroom") || isFullReno) && (
          <Box>
            <Heading fontWeight="medium" fontSize="md" color="black" mb={1}>
              Bathrooms to Renovate
            </Heading>
            <Input
              type="number"
              min={1}
              value={bathrooms}
              onChange={(e) => {
                const raw = e.target.value

                if (raw === '') return
                if (!/^\d+$/.test(raw)) return

                const value = Number(raw)

                if (value >= 0) {
                setBathrooms(value)
                }
              }}
              width="150px"
              textAlign="center"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
            />
          </Box>
        )}
      </VStack>

      {/* ✅ Dynamic Error Message */}
      {showError && errorMessage && (
        <Box display="flex" justifyContent="center">
          <Text
            mt={2}
            fontSize="sm"
            color="red.500"
            width="fit-content"
            textAlign="center"
          >
            {errorMessage}
          </Text>
        </Box>
      )}

      <Box mt={10}>
        <Button
          colorScheme="gray"
          rounded="full"
          onClick={onBack}
          mr={4}
          variant="ghost"
        >
          Back
        </Button>

        <Button
          rounded="full"
          px={8}
          bg={"black"}
          color="white"
          onClick={handleContinue}>
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
