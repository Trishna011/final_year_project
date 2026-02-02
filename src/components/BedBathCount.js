import {
  Box,
  Button,
  Heading,
  VStack,
  Input
} from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function BedBathCount({ onNext, onBack, selected }) {
  const [bedrooms, setBedrooms] = useState(1);
  const [bathrooms, setBathrooms] = useState(1);

  const isFullReno = selected.includes("Full renovation");

  const handleContinue = () => {
    const data = {};

    if (selected.includes("Bedroom") || isFullReno) {
      data.bedrooms_to_reno = bedrooms;
    }

    if (selected.includes("Bathroom") || isFullReno) {
      data.bathrooms_to_reno = bathrooms;
    }

    onNext(data);
  };

  const canContinue =
    ((!selected.includes("Bedroom") && !isFullReno) || bedrooms >= 1) &&
    ((!selected.includes("Bathroom") && !isFullReno) || bathrooms >= 1);

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
              onChange={(e) => setBedrooms(Number(e.target.value))}
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
              onChange={(e) => setBathrooms(Number(e.target.value))}
              width="150px"
              textAlign="center"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
            />
          </Box>
        )}
      </VStack>

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
          bg={canContinue ? "black" : "gray.600"}
          color="white"
          rounded="full"
          px={8}
          opacity={canContinue ? 1 : 0.6}
          cursor={canContinue ? "pointer" : "not-allowed"}
          isDisabled={!canContinue}
          onClick={canContinue ? handleContinue : undefined}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
