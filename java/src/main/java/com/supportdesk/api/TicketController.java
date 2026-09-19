package com.supportdesk.api;
import org.springframework.web.bind.annotation.*; import java.util.*;
@RestController @RequestMapping("/tickets") public class TicketController {
 @GetMapping("/{id}/context") public Map<String,Object> context(@PathVariable String id){return Map.of("ticketId",id,"priority","P2","product","enterprise-vpn");}
}
