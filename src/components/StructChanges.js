import { Box, Button, Heading, SimpleGrid, Text, VStack } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function StructChanges({ onBack, onNext, answers }) {
  const bedroomCount = answers?.bedrooms_to_reno ?? 0;
  const bathroomCount = answers?.bathrooms_to_reno ?? 0;
  const renovationTypes = answers?.renovation_type ?? [];
  const isFullReno = renovationTypes.includes("Full renovation");

  const roomList = isFullReno
    ? ["Full renovation"]
    : [
        ...Array.from({ length: bedroomCount }, (_, i) => `Bedroom ${i + 1}`),
        ...Array.from({ length: bathroomCount }, (_, i) => `Bathroom ${i + 1}`),
        ...renovationTypes.filter(t => !["Bedroom", "Bathroom"].includes(t)),
      ];

  const [selected, setSelected] = useState(Array(roomList.length).fill(null));
  const [showError, setShowError] = useState(false);

  const updateSelection = (index, val) => {
    const next = [...selected];
    next[index] = val;
    setShowError(false);
    setSelected(next);
  };

  const allSelected = selected.every(v => v !== null);

  const handleNext = () => {
    if (!allSelected) {
      setShowError(true);
      return;
    }
    setShowError(false);
    onNext({
      structural_changes: isFullReno ? [selected[0]] : selected
    });
  };

  return (
    <MotionBox
      key="struct-changes"
      initial={{ opacity: 0, y: 80 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -80 }}
      transition={{ duration: 0.6, ease: "easeInOut" }}
      p={8}
      bg="white"
      rounded="2xl"
      shadow="xl"
      maxW="700px"
      textAlign="center"
      color="gray.800"
    >
      <Heading mb={8}>Any structural changes required?</Heading>

      <VStack
        spacing={6}
        w="100%"
        maxH="400px"
        overflowY="auto"
        pr={2}
        sx={{
          "&::-webkit-scrollbar": { width: "6px" },
          "&::-webkit-scrollbar-thumb": { background: "#d1d1d1", borderRadius: "10px" }
        }}
      >
        {roomList.map((name, index) => (
          <Box
            key={index}
            p={6}
            rounded="2xl"
            border="1px solid"
            borderColor="gray.300"
            shadow="md"
            w="100%"
            textAlign="left"
          >
            <Text fontWeight="medium" fontSize="md" color="black" mb={2}>
              {name}
            </Text>

            <SimpleGrid columns={2} spacing={4}>
              {["Yes", "No"].map(option => (
                <MotionBox
                  key={option}
                  p={3}
                  rounded="xl"
                  borderWidth="2px"
                  borderColor={selected[index] === option ? "teal.500" : "gray.300"}
                  bg={selected[index] === option ? "teal.50" : "white"}
                  color={selected[index] === option ? "teal.700" : "black"}
                  cursor="pointer"
                  textAlign="center"
                  whileHover={{ scale: 1.04 }}
                  whileTap={{ scale: 0.97 }}
                  onClick={() => updateSelection(index, option)}
                  transition={{ duration: 0.2 }}
                >
                  {option}
                </MotionBox>
              ))}
            </SimpleGrid>
          </Box>
        ))}
      </VStack>

      {showError && (
        <Box display="flex" justifyContent="center">
          <Text
            mt={2}
            fontSize="sm"
            color="red.500"
            width="fit-content"
            textAlign="center"
          >
            Please answer all rooms before continuing
          </Text>
        </Box>
      )}

      <Box mt={10}>
        <Button variant="ghost" colorScheme="gray" rounded="full" mr={4} onClick={onBack}>
          Back
        </Button>
        <Button
          rounded="full"
          px={8}
          bg="black"
          color="white"
          onClick={handleNext}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}