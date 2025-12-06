import { Box, Button, Heading, VStack, Text } from "@chakra-ui/react";
import { motion } from "framer-motion";
import { useState } from "react";

const MotionBox = motion(Box);

export default function MaterialGrade({ onBack, onNext, answers }) {
  const renovationTypes = answers?.renovation_type ?? [];
  const bedroomCount = answers?.bedrooms_to_reno ?? 0;
  const bathroomCount = answers?.bathrooms_to_reno ?? 0;

  const otherTypes = renovationTypes.filter(
    r => !["Bedroom", "Bathroom"].includes(r)
  );

  // Initialize dynamic selections
  const initialValues = {
    bedrooms: Array(bedroomCount).fill(""),
    bathrooms: Array(bathroomCount).fill(""),
    other: otherTypes.reduce((acc, cur) => ({ ...acc, [cur]: "" }), {})
  };

  const [values, setValues] = useState(initialValues);

  const materialOptions = ["High-end", "Mid-range", "Budget-friendly"];

  const updateSelection = (group, indexOrKey, value) => {
    if (group === "other") {
      setValues(prev => ({
        ...prev,
        other: { ...prev.other, [indexOrKey]: value }
      }));
    } else {
      const updated = [...values[group]];
      updated[indexOrKey] = value;
      setValues(prev => ({ ...prev, [group]: updated }));
    }
  };

  const allSelected =
    values.bedrooms.every(v => v !== "") &&
    values.bathrooms.every(v => v !== "") &&
    Object.values(values.other).every(v => v !== "");

  const handleNext = () => {
    onNext({
      material_grade: {
        bedrooms: values.bedrooms,
        bathrooms: values.bathrooms,
        other: values.other
      }
    });
  };

  return (
    <MotionBox
      key="material-grade"
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
      <Heading mb={8}>Select Material Grade</Heading>

      {/* Scrollable container like your Sqft pages */}
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

        {/* Bedrooms */}
        {values.bedrooms.map((v, i) => (
          <Box key={`bed-${i}`} p={6} rounded="2xl" border="1px solid" borderColor="gray.300" shadow="md" w="100%" textAlign="left">
            <Text fontWeight="medium" mb={2}>Bedroom {i + 1} Material</Text>

            <Box
              as="select"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
              w="100%"
              size="lg"
              px={2.5}
              py={1.5}
              value={v}
              onChange={(e) => updateSelection("bedrooms", i, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
            >
              <option value="">Choose material grade</option>
              {materialOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </Box>
          </Box>
        ))}

        {/* Bathrooms */}
        {values.bathrooms.map((v, i) => (
          <Box key={`bath-${i}`} p={6} rounded="2xl" border="1px solid" borderColor="gray.300" shadow="md" w="100%" textAlign="left">
            <Text fontWeight="medium" mb={2}>Bathroom {i + 1} Material</Text>

            <Box
              as="select"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
              w="100%"
              size="lg"
              px={2.5}
              py={1.5}
              value={v}
              onChange={(e) => updateSelection("bathrooms", i, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
            >
              <option value="">Choose material grade</option>
              {materialOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </Box>
          </Box>
        ))}

        {/* Other renovation types */}
        {Object.keys(values.other).map(room => (
          <Box key={room} p={6} rounded="2xl" border="1px solid" borderColor="gray.300" shadow="md" w="100%" textAlign="left">
            <Text fontWeight="medium" mb={2}>{room} Material</Text>

            <Box
              as="select"
              rounded="full"
              borderWidth="1px"
              borderColor="teal.500"
              w="100%"
              size="lg"
              px={2.5}
              py={1.5}
              value={values.other[room]}
              onChange={(e) => updateSelection("other", room, e.target.value)}
              _hover={{ borderColor: "teal.500" }}
              _focus={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
              _focusVisible={{ borderColor: "teal.500", boxShadow: "none", outline: "none" }}
            >
              <option value="">Choose material grade</option>
              {materialOptions.map(opt => <option key={opt} value={opt}>{opt}</option>)}
            </Box>
          </Box>
        ))}

      </VStack>

      <Box mt={10}>
        <Button variant="ghost" colorScheme="gray" rounded="full" mr={4} onClick={onBack}>
          Back
        </Button>

        <Button
          rounded="full"
          px={8}
          bg={allSelected ? "black" : "gray.600"}
          color="white"
          opacity={allSelected ? 1 : 0.6}
          cursor={allSelected ? "pointer" : "not-allowed"}
          isDisabled={!allSelected}
          onClick={allSelected ? handleNext : undefined}
        >
          Next
        </Button>
      </Box>
    </MotionBox>
  );
}
