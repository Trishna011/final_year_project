import { Box, Button, Heading, SimpleGrid, Text, VStack } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function StructChanges({ onBack, onNext, answers }) {
  const renovationTypes = answers.renovation_type || [];
  const [selected, setSelected] = useState(
    Array(renovationTypes.length).fill(null)
  );

  const updateSelection = (i, val) => {
    const next = [...selected];
    next[i] = val;
    setSelected(next);
  };

  const allSelected = selected.every((v) => v !== null);

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
      textAlign="center"
      maxW="700px"
      color="gray.800"
    >
      <Heading mb={8}>Any structural changes required?</Heading>

      {/* inner card container like MaterialGrade */}
      <VStack spacing={6} w="100%">
        {renovationTypes.map((type, index) => (
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
            <Text fontWeight="medium" fontSize="md" color="black" mb={1}>{type}</Text>

            <SimpleGrid columns={2} spacing={4}>
              {["Yes", "No"].map((option) => (
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

      {/* Navigation */}
      <Box mt={10}>
        <Button
          colorScheme="gray"
          rounded="full"
          mr={4}
          variant="ghost"
          onClick={onBack}
        >
          Back
        </Button>

        <Button
          bg={allSelected ? "black" : "gray.600"}
          color="white"
          rounded="full"
          px={8}
          opacity={allSelected ? 1 : 0.6}
          cursor={allSelected ? "pointer" : "not-allowed"}
          isDisabled={!allSelected}
          onClick={() => allSelected && onNext({ structural_changes: selected })}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
