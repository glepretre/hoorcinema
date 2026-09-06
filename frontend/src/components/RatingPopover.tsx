import { useMutation } from "@tanstack/react-query";
import { Alert, Button, Popover, Rate, Typography } from "antd";
import { useState } from "react";

import { ApiError } from "../api/client";

const { Text } = Typography;

interface RatingPopoverProps {
  label: string;
  onRate: (score: number) => Promise<unknown>;
  onRated: (score: number) => void;
}

function ratingErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 401) {
    return "Votre session a expiré. Reconnectez-vous.";
  }
  if (error instanceof ApiError && error.status === 403) {
    return "Seuls les spectateurs peuvent attribuer une note.";
  }
  return "Impossible d’enregistrer la note. Réessayez.";
}

export function RatingPopover({ label, onRate, onRated }: RatingPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [score, setScore] = useState(0);
  const mutation = useMutation({
    mutationFn: onRate,
    onSuccess: (_rating, submittedScore) => {
      setScore(submittedScore);
      setIsOpen(false);
      onRated(submittedScore);
    },
  });

  return (
    <Popover
      classNames={{ root: "rating-popover" }}
      trigger="click"
      open={isOpen}
      onOpenChange={(open) => {
        if (!mutation.isPending) {
          setIsOpen(open);
          if (open) {
            mutation.reset();
          }
        }
      }}
      content={
        <div className="rating-popover-content">
          <Text strong>{label}</Text>
          <Rate
            value={score}
            disabled={mutation.isPending}
            tooltips={[
              "1 étoile",
              "2 étoiles",
              "3 étoiles",
              "4 étoiles",
              "5 étoiles",
            ]}
            onChange={(nextScore) => mutation.mutate(nextScore)}
          />
          {mutation.isPending ? (
            <Text type="secondary">Enregistrement…</Text>
          ) : null}
          {mutation.isError ? (
            <Alert
              type="error"
              showIcon
              title={ratingErrorMessage(mutation.error)}
            />
          ) : null}
        </div>
      }
    >
      <Button
        className="rating-trigger"
        size="small"
        aria-label={
          score > 0 ? `${label}, note actuelle ${score} sur 5` : label
        }
      >
        {score > 0 ? `Votre note : ${score} / 5` : "Noter"}
      </Button>
    </Popover>
  );
}
