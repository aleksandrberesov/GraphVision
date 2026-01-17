import { Box } from "@chakra-ui/react";

export default function MouseTracker({ onMove }) {
  const handleMove = (e) => {
    if (onMove) {
      onMove({ x: e.clientX, y: e.clientY });
    }
  };

  return (
    <Box w="100%" h="400px" border="2px solid gray" onMouseMove={handleMove}>
      Move your mouse here
    </Box>
  );
}