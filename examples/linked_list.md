# Few-Shot：单向链表删除节点

> 同一个问题，两种品味。区别不在代码长短，而在**特例的数量**。

## 问题

从单向链表中删除第一个 `data == target` 的节点。必须覆盖的边界：删除头节点、删除中间节点、删除尾节点、目标不存在、空链表。

## Bad Taste：prev 指针 + 头节点特判

```c
#include <stdlib.h>

typedef struct node {
    void *data;
    struct node *next;
} node_t;

/* 平庸写法：用 prev 记录前驱，对头节点单独开一条处理路径 */
void remove_node(node_t **head, const void *target) {
    node_t *prev = NULL;
    node_t *cur = *head;

    while (cur != NULL) {
        if (cur->data == target) {
            if (prev != NULL)
                prev->next = cur->next;   // 中间/尾部节点：改前驱的 next
            else
                *head = cur->next;        // 特判：删除的恰好是头节点
            free(cur);
            return;
        }
        prev = cur;
        cur = cur->next;
    }
}
```

病根：删除动作的本质只有一个——"重写指向受害者的那条链接"。这里却被劈成两条路径，头节点需要专属分支。多维护一个状态变量 `prev`，就多一整类状态不一致的可能。

## Good Taste：指向指针的指针

```c
#include <stdlib.h>

typedef struct node {
    void *data;
    struct node *next;
} node_t;

/*
 * 好品味：indirect 指向"指向当前节点的那个指针"。
 * 它一开始就指向 head 本身（indirect = &head）；之后指向上一节点的 next 字段。
 * 于是 head 与任意节点的 next 在结构上完全同构。
 */
void remove_node(node_t **head, const void *target) {
    node_t **indirect = head;          // 即 &head：头节点的链接也只是一条链接

    while (*indirect != NULL) {
        node_t *victim = *indirect;
        if (victim->data == target) {
            *indirect = victim->next;  // 不关心受害者在头部、中间还是尾部
            free(victim);
            return;
        }
        indirect = &victim->next;     // 移动到"下一条链接"，而非下一个节点
    }
}
```

调用方式：`remove_node(&head, target);`

## Agent 点评：为什么后者更好

- **特例归零**：头节点、中间节点、尾节点走同一条赋值 `*indirect = victim->next`；空链表与未命中自然落在 `while` 条件里。五类边界，零个特判分支。
- **模型正确**：链表的本质不是"一串节点"，而是"一串指向下一节点的**链接**"。`prev` 写法站在节点层面思考，于是头节点"没有前驱"成为漏洞；`indirect` 写法站在链接层面思考——而每条链接，包括 `head`，结构完全相同。
- **删除即重写**：合适的数据结构（指向指针的指针）让"删除"还原为它的本质动作：改写一个指针。当没有任何数据结构能让逻辑更简单时，代码才算触底。
- 这就是好品味：不是更短的代码，而是**代码里根本不存在需要特判的位置**。
