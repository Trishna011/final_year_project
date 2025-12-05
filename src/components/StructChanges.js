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
    <Box p={4} maxW="1000px" mx="auto" color="gray.800">
      
      <VStack spacing={6} w="100%">
        {renovationTypes.map((type, index) => (
          <MotionBox
            key={`struct-${index}`}
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -40 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            p={6}
            w="100%"
            maxW="400px"
            bg="white"
            rounded="2xl"
            shadow="md"
            border="1px solid"
            borderColor="gray.200"
            overflow="auto"
        
          >
            <Text fontSize="lg" fontWeight="semibold" mb={3}>
              {type}
            </Text>

            <Text fontSize="md" color="gray.600" mb={4}>
              Any structural changes?
            </Text>

            <SimpleGrid columns={2} spacing={4}>
              {["Yes", "No"].map((option) => (
                <MotionBox
                  key={option}
                  p={3}
                  rounded="xl"
                  borderWidth="2px"
                  borderColor={
                    selected[index] === option ? "teal.500" : "gray.300"
                  }
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
          </MotionBox>
        ))}
      </VStack>

      {/* NAVIGATION */}
      <Box textAlign="center" mt={10}>
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
          cursor={allSelected ? "pointer" : "not-allowed"}
          opacity={!allSelected ? 0.6 : 1}
          px={8}
          isDisabled={!allSelected}
          onClick={() => allSelected && onNext({ structural_changes: selected })}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
}
