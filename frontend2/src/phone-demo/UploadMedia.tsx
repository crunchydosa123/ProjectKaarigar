import { usePage } from "@/contexts/PageContext";
import { House, LucideImagePlus, LucideVideo } from "lucide-react";
import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";

type Props = {};

const UploadMedia = (props: Props) => {
  const { setCurrentPage } = usePage();
  const [selectedProduct, setSelectedProduct] = useState<string | undefined>();
  const [openPopover, setOpenPopover] = useState(false);
  const [mediaType, setMediaType] = useState<"photo" | "video" | null>(null);

  const products = ["Product A", "Product B", "Product C"];
  const placeholderImages = [
    "/placeholder.png",
    "/placeholder2.png",
    "/placeholder3.png",
  ];

  const handleAddMedia = (type: "photo" | "video") => {
    setMediaType(type);
    setOpenPopover(true);
  };

  return (
    <div
      className="w-full h-full bg-cover bg-center flex flex-col overflow-y-auto overflow-x-hidden"
      style={{ backgroundImage: "url('/white_bg.png')" }}
    >
      {/* Header */}
      <div className="w-full mt-10 flex justify-start items-center p-3">
        <button
          className="h-10 w-10 bg-gray-500 rounded-md flex justify-center items-center text-white"
          onClick={() => setCurrentPage("home")}
        >
          <House />
        </button>
        <div className="text-md font-bold ml-3">Upload Product Media</div>
      </div>

      {/* Product Dropdown */}
      <div className="mt-5 px-5">
        <Label className="mb-1" >Name of Image/Video</Label>
        <Input value={'seedhe pot'} />
      </div>

      {/* Media Buttons */}
      <div className="mt-5 px-5 flex justify-center gap-2 w-full">
        <Button className="w-1/2 h-30 flex-col" variant={'outline'}  onClick={() => handleAddMedia("photo")}>
          <LucideImagePlus />
          <div>Add Photo</div>
        </Button>
        <Button className="w-1/2 h-30 flex-col" variant={'outline'}  onClick={() => handleAddMedia("video")}>
          <LucideVideo />
          <div>Add Video</div>
        </Button>
        </div>
      {/* Popover for Import */}
      <Popover open={openPopover} onOpenChange={setOpenPopover}>
        <PopoverTrigger>
          {/* Hidden trigger, we open programmatically */}
          <div />
        </PopoverTrigger>
        <PopoverContent className="w-96 p-4">
          <Card>
            <CardHeader>
              <CardTitle>
                {mediaType === "photo" ? "Add Photo" : "Add Video"}
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-col gap-3">
              <Button
                variant="outline"
                onClick={() => alert("Open device import (placeholder)")}
              >
                Import from device
              </Button>

              <div className="grid grid-cols-3 gap-2">
                {placeholderImages.map((img) => (
                  <img
                    key={img}
                    src={img}
                    alt="placeholder"
                    className="w-full h-24 object-cover border border-gray-300 rounded-md"
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        </PopoverContent>
      </Popover>
    </div>
  );
};

export default UploadMedia;
