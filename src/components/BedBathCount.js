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

  const handleContinue = () => {
    const data = {};

    if (selected.includes("Bedroom")) data.bedrooms_to_reno = bedrooms;
    if (selected.includes("Bathroom")) data.bathrooms_to_reno = bathrooms;

    onNext(data);
  };

  // 🔥 User must enter 1+ in each selected category
  const canContinue =
    (!selected.includes("Bedroom") || bedrooms >= 1) &&
    (!selected.includes("Bathroom") || bathrooms >= 1);

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
        {selected.includes("Bedroom") && (
          <Box>
            <Heading fontWeight="medium" fontSize="md" color="black" mb={1}>Bedrooms to Renovate</Heading>
            <Input
              type="number"
              min={1}
              value={bedrooms}
              onChange={(e)=> setBedrooms(Number(e.target.value))}
              width="150px"
              textAlign="center"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
              _hover={{ borderColor: "teal.500" }}
              _focus={{
                borderColor: "teal.500",
                boxShadow: "none",      // removes thick halo/glow
                outline: "none"         // removes browser highlighting fallback
              }}

              _focusVisible={{
                borderColor: "teal.500",
                boxShadow: "none",
                outline: "none"
              }}

              transition="all .2s"
            />
          </Box>
        )}

        {selected.includes("Bathroom") && (
          <Box>
            <Heading fontWeight="medium" fontSize="md" color="black" mb={1}>Bathrooms to Renovate</Heading>
            <Input
              type="number"
              min={1}
              value={bathrooms}
              onChange={(e)=> setBathrooms(Number(e.target.value))}
              width="150px"
              textAlign="center"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
              _hover={{ borderColor: "teal.500" }}
              _focus={{
                borderColor: "teal.500",
                boxShadow: "none",      // removes thick halo/glow
                outline: "none"         // removes browser highlighting fallback
              }}

              _focusVisible={{
                borderColor: "teal.500",
                boxShadow: "none",
                outline: "none"
              }}

              transition="all .2s"
            />
          </Box>
        )}
      </VStack>

      {/* Buttons match your Location screen */}
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
          bg={!canContinue ? "gray.600" : "black"}
          color="white"
          rounded="full"
          px={8}
          opacity={!canContinue ? 0.6 : 1}
          cursor={!canContinue ? "not-allowed" : "pointer"}
          isDisabled={!canContinue}
          onClick={canContinue ? handleContinue : undefined}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
